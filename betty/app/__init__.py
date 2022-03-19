from __future__ import annotations

import weakref
from collections import OrderedDict
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import AsyncExitStack, suppress, contextmanager
from gettext import NullTranslations
from tempfile import TemporaryDirectory
from typing import List, Optional, Type, Sequence, Any, Iterable, TYPE_CHECKING, Set
from urllib.parse import urlparse

from babel.core import parse_locale, Locale

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher
from betty.asyncio import sync
from betty.environment import Environment
from betty.error import ensure_context
from betty.model import Entity, EntityTypeProvider
from betty.model.event_type import EventTypeProvider, Birth, Baptism, Adoption, Death, Funeral, Cremation, Burial, Will, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Occupation, Retirement, Correspondence, Confirmation
from betty.os import PathLike

if TYPE_CHECKING:
    from betty.url import StaticUrlGenerator, ContentNegotiationUrlGenerator

from betty.importlib import import_any

try:
    from graphlib import TopologicalSorter, CycleError
except ImportError:
    from graphlib_backport import TopologicalSorter
from pathlib import Path

import aiohttp
from jinja2 import Environment as Jinja2Environment
from reactives import reactive, scope

from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.dispatch import Dispatcher
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

from betty.model.ancestry import Ancestry, Citation, Event, File, Person, PersonName, Presence, Place, Enclosure, \
    Source, Note, EventType
from betty.config import Configurable, Configuration as GenericConfiguration, ConfigurationError, ensure_path, ensure_directory_path
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH
from betty.locale import Translations, negotiate_locale, TranslationsRepository


@reactive
class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: List[List[Extension]]) -> None:
        self._extensions = extensions
        self.react.trigger()


@reactive
class AppExtensionConfiguration:
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, extension_configuration: Optional[GenericConfiguration] = None):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(extension_type, Configurable):
            extension_configuration = extension_type.configuration_type().default()
        if extension_configuration is not None:
            extension_configuration.react(self)
        self._extension_configuration = extension_configuration

    def __repr__(self):
        return '<%s.%s(%s)>' % (self.__class__.__module__, self.__class__.__name__, self.extension_type)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.extension_type != other.extension_type:
            return False
        if self.enabled != other.enabled:
            return False
        if self.extension_configuration != other.extension_configuration:
            return False
        return True

    @property
    def extension_type(self) -> Type[Extension]:
        return self._extension_type

    @reactive
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Optional[Configuration]:
        return self._extension_configuration


class AppExtensionsConfiguration(GenericConfiguration):
    def __init__(self, configurations: Optional[Iterable[AppExtensionConfiguration]] = None):
        super().__init__()
        self._configurations = OrderedDict()
        if configurations is not None:
            for configuration in configurations:
                self.add(configuration)

    @scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> AppExtensionConfiguration:
        return self._configurations[extension_type]

    def __delitem__(self, extension_type: Type[Extension]) -> None:
        with suppress(KeyError):
            self._configurations[extension_type].react.shutdown(self)
        del self._configurations[extension_type]
        self.react.trigger()

    @scope.register_self
    def __iter__(self) -> Iterable[AppExtensionConfiguration]:
        return (configuration for configuration in self._configurations.values())

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other):
        if not isinstance(other, AppExtensionsConfiguration):
            return NotImplemented
        return self._configurations == other._configurations

    def add(self, configuration: AppExtensionConfiguration) -> None:
        self._configurations[configuration.extension_type] = configuration
        configuration.react(self)
        self.react.trigger()

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('App extensions configuration must be a mapping (dictionary).')

        for extension_type in self._configurations:
            del self[extension_type]

        for extension_type_name in dumped_configuration:
            with ensure_context(f'`{extension_type_name}`'):
                try:
                    extension_type = import_any(extension_type_name)
                except ImportError as e:
                    raise ConfigurationError(e)

                if not issubclass(extension_type, Extension):
                    raise ConfigurationError('"%s" is not a Betty extension.' % extension_type_name)

                dumped_extension_configuration = dumped_configuration[extension_type_name]

                if not isinstance(dumped_extension_configuration, dict):
                    raise ConfigurationError('The configuration must be a mapping (dictionary).')

                if 'enabled' in dumped_extension_configuration:
                    if not isinstance(dumped_extension_configuration['enabled'], bool):
                        raise ConfigurationError(
                            'The extension must be declared enabled (true) or disabled (false).',
                            contexts=['`enabled`'],
                        )
                    enabled = dumped_extension_configuration['enabled']
                else:
                    enabled = True

                if 'configuration' in dumped_extension_configuration:
                    if not issubclass(extension_type, Configurable):
                        raise ConfigurationError(f'{extension_type_name} is not configurable.', contexts=['`configuration`'])
                    extension_configuration = extension_type.configuration_type().default()
                    extension_configuration.load(dumped_extension_configuration['configuration'])
                else:
                    extension_configuration = None

                self.add(AppExtensionConfiguration(
                    extension_type,
                    enabled,
                    extension_configuration,
                ))

    def dump(self) -> Any:
        dumped_configuration = {}
        for app_extension_configuration in self:
            extension_type = app_extension_configuration.extension_type
            dumped_configuration[extension_type.name()] = {
                'enabled': app_extension_configuration.enabled,
            }
            if issubclass(extension_type, Configurable):
                dumped_configuration[extension_type.name()]['configuration'] = app_extension_configuration.extension_configuration.dump()
        return dumped_configuration


class LocaleConfiguration:
    def __init__(self, locale: str, alias: str = None):
        self._locale = locale
        self._alias = alias

    def __repr__(self):
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.locale, self.alias)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.locale != other.locale:
            return False
        if self.alias != other.alias:
            return False
        return True

    def __hash__(self):
        return hash((self._locale, self._alias))

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def alias(self) -> str:
        if self._alias is None:
            return self.locale
        return self._alias


class LocalesConfiguration(GenericConfiguration):
    def __init__(self, configurations: Optional[Sequence[LocaleConfiguration]] = None):
        super().__init__()
        self._configurations = OrderedDict()
        self.replace(configurations)

    @scope.register_self
    def __getitem__(self, locale: str) -> LocaleConfiguration:
        return self._configurations[locale]

    def __delitem__(self, locale: str) -> None:
        if len(self._configurations) <= 1:
            raise ConfigurationError('Cannot remove the last remaining locale %s' % Locale.parse(locale, '-').get_display_name())
        del self._configurations[locale]
        self.react.trigger()

    @scope.register_self
    def __iter__(self) -> Iterable[LocaleConfiguration]:
        return (configuration for configuration in self._configurations.values())

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other):
        if not isinstance(other, LocalesConfiguration):
            return NotImplemented
        return self._configurations == other._configurations

    @scope.register_self
    def __contains__(self, item):
        return item in self._configurations

    @scope.register_self
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(list(self._configurations.values())))

    def add(self, configuration: LocaleConfiguration) -> None:
        self._configurations[configuration.locale] = configuration
        self.react.trigger()

    def replace(self, configurations: Optional[Sequence[LocaleConfiguration]] = None) -> None:
        self._configurations.clear()
        if configurations is None or len(configurations) < 1:
            configurations = [LocaleConfiguration('en-US')]
        for configuration in configurations:
            self._configurations[configuration.locale] = configuration
        self.react.trigger()

    @reactive
    @property
    def default(self) -> Optional[LocaleConfiguration]:
        try:
            return next(iter(self._configurations.values()))
        except StopIteration:
            return None

    @default.setter
    def default(self, configuration: LocaleConfiguration) -> None:
        self._configurations[configuration.locale] = configuration
        self._configurations.move_to_end(configuration.locale, False)
        self.react.trigger()

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, list):
            raise ConfigurationError('Locales configuration much be a list.')

        if len(dumped_configuration) > 0:
            self._configurations.clear()
            for dumped_locale_configuration in dumped_configuration:
                locale = dumped_locale_configuration['locale']
                parse_locale(locale, '-')
                self.add(LocaleConfiguration(
                    locale,
                    dumped_locale_configuration['alias'] if 'alias' in dumped_locale_configuration else None,
                ))

    def dump(self) -> Any:
        dumped_configuration = []
        for locale_configuration in self:
            dumped_locale_configuration = {
                'locale': locale_configuration.locale,
            }
            if locale_configuration.alias != locale_configuration.locale:
                dumped_locale_configuration['alias'] = locale_configuration.alias
            dumped_configuration.append(dumped_locale_configuration)
        return dumped_configuration


class ThemeConfiguration(GenericConfiguration):
    def __init__(self):
        super().__init__()
        self._background_image_id = None

    @reactive
    @property
    def background_image_id(self) -> Optional[str]:
        return self._background_image_id

    @background_image_id.setter
    def background_image_id(self, background_image_id: Optional[str]) -> None:
        self._background_image_id = background_image_id

    def load(self, dumped_configuration: Any) -> None:
        for key, value in dumped_configuration.items():
            setattr(self, key, value)

    def dump(self) -> Any:
        dumped_configuration = {
            'background_image_id': self.background_image_id
        }
        return dumped_configuration


class Configuration(GenericConfiguration):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self._default_output_directory = TemporaryDirectory()
        weakref.finalize(self, self._default_output_directory.cleanup)
        self.output_directory_path = self._default_output_directory.name
        self.base_url = 'https://example.com' if base_url is None else base_url
        self.root_path = '/'
        self.clean_urls = False
        self.content_negotiation = False
        self.title = 'Betty'
        self.author = None
        self._extensions = AppExtensionsConfiguration()
        self._extensions.react(self)
        self._debug = False
        self.assets_directory_path = None
        self._locales = LocalesConfiguration()
        self._locales.react(self)
        self._theme = ThemeConfiguration()
        self._theme.react(self)
        self.lifetime_threshold = 125

    @reactive
    @property
    def output_directory_path(self) -> Path:
        return self._output_directory_path

    @output_directory_path.setter
    def output_directory_path(self, output_directory_path: PathLike) -> None:
        self._output_directory_path = Path(output_directory_path)

    @reactive
    @property
    def assets_directory_path(self) -> Optional[str]:
        return self._assets_directory_path

    @assets_directory_path.setter
    def assets_directory_path(self, assets_directory_path: Optional[str]) -> None:
        self._assets_directory_path = assets_directory_path

    @reactive
    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @reactive
    @property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: Optional[str]) -> None:
        self._author = author

    @property
    def www_directory_path(self) -> Path:
        return self.output_directory_path / 'www'

    @reactive
    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str):
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise ConfigurationError('The base URL must start with a scheme such as https://, http://, or file://.')
        if not base_url_parts.netloc:
            raise ConfigurationError('The base URL must include a path.')
        self._base_url = '%s://%s' % (base_url_parts.scheme, base_url_parts.netloc)

    @reactive
    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str):
        self._root_path = root_path.strip('/')

    @reactive
    @property
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    @content_negotiation.setter
    def content_negotiation(self, content_negotiation: bool):
        self._content_negotiation = content_negotiation

    @reactive
    @property
    def clean_urls(self) -> bool:
        return self._clean_urls or self.content_negotiation

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool):
        self._clean_urls = clean_urls

    @reactive
    @property
    def locales(self) -> LocalesConfiguration:
        return self._locales

    @property
    def multilingual(self) -> bool:
        return len(self.locales) > 1

    @property
    def extensions(self) -> AppExtensionsConfiguration:
        return self._extensions

    @reactive
    @property
    def theme(self) -> ThemeConfiguration:
        return self._theme

    @reactive
    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug

    @reactive
    @property
    def lifetime_threshold(self) -> int:
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int):
        if lifetime_threshold < 1:
            raise ConfigurationError('The lifetime threshold must be a positive number.')
        self._lifetime_threshold = lifetime_threshold

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('Betty configuration must be a mapping (dictionary).')

        if 'output' not in dumped_configuration or not isinstance(dumped_configuration['output'], str):
            raise ConfigurationError('The output directory path is required and must be a string.', contexts=['`output`'])
        with ensure_context('`output`'):
            self.output_directory_path = ensure_path(dumped_configuration['output'])

        if 'base_url' not in dumped_configuration or not isinstance(dumped_configuration['base_url'], str):
            raise ConfigurationError('The base URL is required and must be a string.', contexts=['`base_url`'])
        self.base_url = dumped_configuration['base_url']

        if 'title' in dumped_configuration:
            if not isinstance(dumped_configuration['title'], str):
                raise ConfigurationError('The title must be a string.', contexts=['`title`'])
            self.title = dumped_configuration['title']

        if 'author' in dumped_configuration:
            if not isinstance(dumped_configuration['author'], str):
                raise ConfigurationError('The author must be a string.', contexts=['`author`'])
            self.author = dumped_configuration['author']

        if 'root_path' in dumped_configuration:
            if not isinstance(dumped_configuration['root_path'], str):
                raise ConfigurationError('The root path must be a string.', contexts=['`root_path`'])
            self.root_path = dumped_configuration['root_path']

        if 'clean_urls' in dumped_configuration:
            if not isinstance(dumped_configuration['clean_urls'], bool):
                raise ConfigurationError('Clean URLs must be enabled (true) or disabled (false) with a boolean.', contexts=['`clean_urls`'])
            self.clean_urls = dumped_configuration['clean_urls']

        if 'content_negotiation' in dumped_configuration:
            if not isinstance(dumped_configuration['content_negotiation'], bool):
                raise ConfigurationError('Content negotiation must be enabled (true) or disabled (false) with a boolean.', contexts=['`content_negotiation`'])
            self.content_negotiation = dumped_configuration['content_negotiation']

        if 'debug' in dumped_configuration:
            if not isinstance(dumped_configuration['debug'], bool):
                raise ConfigurationError('Debugging must be enabled (true) or disabled (false) with a boolean.', contexts=['`debug`'])
            self.debug = dumped_configuration['debug']

        if 'assets' in dumped_configuration:
            if not isinstance(dumped_configuration['assets'], str):
                raise ConfigurationError('The assets directory path must be a string.', contexts=['`assets`'])
            with ensure_context('`assets`'):
                self.assets_directory_path = ensure_directory_path(dumped_configuration['assets'])

        if 'lifetime_threshold' in dumped_configuration:
            if not isinstance(dumped_configuration['lifetime_threshold'], int):
                raise ConfigurationError('The lifetime threshold must be an integer.', contexts=['`lifetime_threshold`'])
            self.lifetime_threshold = dumped_configuration['lifetime_threshold']

        if 'locales' in dumped_configuration:
            with ensure_context('`locales`'):
                self._locales.load(dumped_configuration['locales'])

        if 'extensions' in dumped_configuration:
            with ensure_context('`extensions`'):
                self._extensions.load(dumped_configuration['extensions'])

        if 'theme' in dumped_configuration:
            with ensure_context('`theme`'):
                self._theme.load(dumped_configuration['theme'])

    def dump(self) -> Any:
        dumped_configuration = {
            'output': str(self.output_directory_path),
            'base_url': self.base_url,
            'title': self.title,
        }
        if self.root_path is not None:
            dumped_configuration['root_path'] = self.root_path
        if self.clean_urls is not None:
            dumped_configuration['clean_urls'] = self.clean_urls
        if self.author is not None:
            dumped_configuration['author'] = self.author
        if self.content_negotiation is not None:
            dumped_configuration['content_negotiation'] = self.content_negotiation
        if self.debug is not None:
            dumped_configuration['debug'] = self.debug
        if self.assets_directory_path is not None:
            dumped_configuration['assets'] = str(self.assets_directory_path)
        dumped_configuration['locales'] = self.locales.dump()
        dumped_configuration['extensions'] = self.extensions.dump()
        if self.lifetime_threshold is not None:
            dumped_configuration['lifetime_threshold'] = self.lifetime_threshold
        dumped_configuration['theme'] = self.theme.dump()

        return dumped_configuration


class App(Configurable[Configuration], Environment):
    def __init__(self):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(Configuration())

        self._active = False
        self._extensions = None
        self._ancestry = Ancestry()
        self._assets = FileSystem()
        self._dispatcher = None
        self._entity_types = None
        self._event_types = None
        self._url_generator = AppUrlGenerator(self)
        self._static_url_generator = StaticPathUrlGenerator(self.configuration)
        self._debug = None
        self._locale = None
        self._translations = TranslationsRepository(self.assets)
        self._default_translations = None
        self._activation_exit_stack = AsyncExitStack()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return Configuration

    def wait(self) -> None:
        self._wait_for_threads()

    def _wait_for_threads(self) -> None:
        if self._executor:
            self._executor.wait()

    def _assert_active(self) -> None:
        if not self._active:
            raise RuntimeError('This application is not yet active.')

    def _assert_deactive(self) -> None:
        if self._active:
            raise RuntimeError('This application is still active.')

    @contextmanager
    def activate_locale(self, requested_locale: str) -> None:
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        self._assert_active()

        negotiated_locale = negotiate_locale(
            requested_locale,
            [
                locale_configuration.locale
                for locale_configuration
                in self.configuration.locales
            ],
        )

        if negotiated_locale is None:
            raise ValueError(f'Locale "{requested_locale}" is not enabled.')

        previous_locale = self._locale
        if negotiated_locale == previous_locale:
            yield
            return
        self._wait_for_threads()

        self._locale = negotiated_locale
        with self.translations[negotiated_locale]:
            self.react.getattr('locale').react.trigger()
            yield
            self._wait_for_threads()

        self._locale = previous_locale
        self.react.getattr('locale').react.trigger()

    async def activate(self) -> None:
        self._assert_deactive()
        self._active = True

        self._wait_for_threads()

        try:
            # Enable the gettext API by entering a dummy translations context.
            self._activation_exit_stack.enter_context(Translations(NullTranslations()))
            # Then enter the final locale context (doing so may recursively require the gettext API).
            self._activation_exit_stack.enter_context(self.activate_locale(self.locale))
            for extension in self.extensions.flatten():
                await extension.activate()
                self._activation_exit_stack.push_async_callback(extension.deactivate)
        except BaseException:
            await self.deactivate()
            raise

    async def deactivate(self) -> None:
        self._assert_active()
        self._active = False

        self._wait_for_threads()

        await self._activation_exit_stack.aclose()

    async def __aenter__(self) -> App:
        await self.activate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.deactivate()

    @reactive
    @property
    def debug(self) -> bool:
        if self._debug is not None:
            return self._debug
        return self._configuration.debug

    @reactive
    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self._configuration.locales.default.locale

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def extensions(self) -> Extensions:
        if self._extensions is None:
            self._extensions = _AppExtensions()
            self._update_extensions()
            self._configuration.extensions.react(self._update_extensions)

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = set()
        for app_extension_configuration in self._configuration.extensions:
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.requires().assert_met()
                extension_types_enabled_in_configuration.add(app_extension_configuration.extension_type)

        extension_types_sorter = TopologicalSorter(
            build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        try:
            extension_types_sorter.prepare()
        except CycleError:
            raise CyclicDependencyError([app_extension_configuration.extension_type for app_extension_configuration in self._configuration.extensions])

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                if issubclass(extension_type, Configurable):
                    if extension_type not in extension_types_enabled_in_configuration or self._configuration.extensions[extension_type].extension_configuration is None:
                        configuration = extension_type.default()
                    else:
                        configuration = self._configuration.extensions[extension_type].extension_configuration
                    extension = extension_type(self, configuration)
                else:
                    extension = extension_type(self)
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(extensions_batch)
        self._extensions._update(extensions)

    @reactive
    @property
    def assets(self) -> FileSystem:
        if len(self._assets) == 0:
            self._assets.prepend(ASSETS_DIRECTORY_PATH, 'utf-8')
            for extension in self.extensions.flatten():
                if extension.assets_directory_path() is not None:
                    self._assets.prepend(extension.assets_directory_path(), 'utf-8')
            if self._configuration.assets_directory_path:
                self._assets.prepend(self._configuration.assets_directory_path)

        return self._assets

    @assets.deleter
    def assets(self) -> None:
        self._assets.clear()

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def url_generator(self) -> ContentNegotiationUrlGenerator:
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @property
    def translations(self) -> TranslationsRepository:
        return self._translations

    @reactive
    @property
    def jinja2_environment(self) -> Jinja2Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import Environment
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @jinja2_environment.deleter
    def jinja2_environment(self) -> None:
        self._jinja2_environment = None

    @reactive
    @property
    def renderer(self) -> Renderer:
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer

            self._renderer = SequentialRenderer([
                Jinja2Renderer(self.jinja2_environment, self._configuration),
            ])

        return self._renderer

    @renderer.deleter
    def renderer(self) -> None:
        self._renderer = None

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            self._executor = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        return self._executor

    @property
    def locks(self) -> Locks:
        return self._locks

    @property
    def http_client(self) -> aiohttp.ClientSession:
        if not self._http_client:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
            weakref.finalize(self, sync(self._http_client.close))
        return self._http_client

    @reactive
    @property
    @sync
    async def entity_types(self) -> Set[Type[Entity]]:
        if self._entity_types is None:
            self._entity_types = set(await self.dispatcher.dispatch(EntityTypeProvider)()) | {
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            }
        return self._entity_types

    @reactive
    @property
    @sync
    async def event_types(self) -> Set[Type[EventType]]:
        if self._event_types is None:
            self._event_types = set(await self.dispatcher.dispatch(EventTypeProvider)()) | {
                Birth,
                Baptism,
                Adoption,
                Death,
                Funeral,
                Cremation,
                Burial,
                Will,
                Engagement,
                Marriage,
                MarriageAnnouncement,
                Divorce,
                DivorceAnnouncement,
                Residence,
                Immigration,
                Emigration,
                Occupation,
                Retirement,
                Correspondence,
                Confirmation,
            }
        return self._event_types

    @entity_types.deleter
    def entity_types(self) -> None:
        self._entity_types = None
