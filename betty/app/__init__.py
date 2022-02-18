from __future__ import annotations

from collections import defaultdict, OrderedDict
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from gettext import NullTranslations
from typing import Dict, List, Optional, Type, Sequence, Any, Iterable, TYPE_CHECKING
from urllib.parse import urlparse

from babel.core import parse_locale, Locale

from betty import fs, os
from betty.app.extension import ListExtensions, Extension, ConfigurableExtension, Extensions, \
    build_extension_type_graph, ExtensionDispatcher
from betty.environment import Environment
from betty.error import ensure_context

if TYPE_CHECKING:
    from betty.url import StaticUrlGenerator, LocalizedUrlGenerator

from betty.importlib import import_any

try:
    from graphlib import TopologicalSorter
except ImportError:
    from graphlib_backport import TopologicalSorter
from pathlib import Path

import aiohttp
from jinja2 import Environment as Jinja2Environment
from reactives import reactive, scope

from betty.concurrent import ExceptionRaisingExecutor
from betty.dispatch import Dispatcher
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

from betty.model.ancestry import Ancestry
from betty.config import Configurable, Configuration as GenericConfiguration, ConfigurationError, ensure_path, ensure_directory_path
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH
from betty.locale import open_translations, Translations, negotiate_locale


@reactive
class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: List[List[Extension]]) -> None:
        self._extensions = extensions
        self.react.trigger()


@reactive
class AppExtensionConfiguration:
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, extension_configuration: Optional[Configuration] = None):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(extension_type, ConfigurableExtension):
            extension_configuration = extension_type.default_configuration()
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

    def _wire(self, value) -> None:
        value.react(self)

    def _unwire(self, value) -> None:
        value.react.shutdown(self)

    @scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> AppExtensionConfiguration:
        return self._configurations[extension_type]

    def __delitem__(self, extension_type: Type[Extension]) -> None:
        with suppress(KeyError):
            self._unwire(self._configurations[extension_type])
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
        self._wire(configuration)
        self.react.trigger()

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('App extensions configuration must be a mapping (dictionary).')

        loaded_extension_configuration = []
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
                    if not issubclass(extension_type, ConfigurableExtension):
                        raise ConfigurationError(f'{extension_type_name} is not configurable.', contexts=['`configuration`'])
                    extension_configuration = extension_type.configuration_type().load(dumped_extension_configuration['configuration'])
                else:
                    extension_configuration = None

                loaded_extension_configuration.append(AppExtensionConfiguration(
                    extension_type,
                    enabled,
                    extension_configuration,
                ))

        return cls(loaded_extension_configuration)

    def dump(self) -> Any:
        dumped_configuration = {}
        for app_extension_configuration in self:
            extension_type = app_extension_configuration.extension_type
            dumped_configuration[extension_type.name()] = {
                'enabled': app_extension_configuration.enabled,
            }
            if issubclass(extension_type, ConfigurableExtension):
                dumped_configuration[extension_type.name()]['configuration'] = extension_type.configuration_type().dump(app_extension_configuration.extension_configuration)
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

    @classmethod
    def load(cls, dumped_configuration: Any) -> LocalesConfiguration:
        if not isinstance(dumped_configuration, list):
            raise ConfigurationError('Locales configuration much be a list.')

        loaded_configuration = cls()
        if len(dumped_configuration) > 0:
            loaded_configuration._configurations.clear()
            for dumped_locale_configuration in dumped_configuration:
                locale = dumped_locale_configuration['locale']
                parse_locale(locale, '-')
                loaded_configuration.add(LocaleConfiguration(
                    locale,
                    dumped_locale_configuration['alias'] if 'alias' in dumped_locale_configuration else None,
                ))
        return loaded_configuration

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

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        loaded_configuration = cls()

        for key, value in dumped_configuration.items():
            setattr(loaded_configuration, key, value)

        return loaded_configuration

    def dump(self) -> Any:
        dumped_configuration = {
            'background_image_id': self.background_image_id
        }
        return dumped_configuration


class Configuration(GenericConfiguration):
    def __init__(self, output_directory_path: os.PathLike, base_url: str):
        super().__init__()
        self.cache_directory_path = fs.CACHE_DIRECTORY_PATH
        self.output_directory_path = Path(output_directory_path)
        self.base_url = base_url
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
    def output_directory_path(self) -> str:
        return self._output_directory_path

    @output_directory_path.setter
    def output_directory_path(self, output_directory_path: str) -> None:
        self._output_directory_path = output_directory_path

    @reactive
    @property
    def assets_directory_path(self) -> Optional[str]:
        return self._assets_directory_path

    @assets_directory_path.setter
    def assets_directory_path(self, assets_directory_path: Optional[str]) -> None:
        self._assets_directory_path = assets_directory_path

    @reactive
    @property
    def cache_directory_path(self) -> str:
        return self._cache_directory_path

    @cache_directory_path.setter
    def cache_directory_path(self, cache_directory_path: str) -> None:
        self._cache_directory_path = cache_directory_path

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

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('Betty configuration must be a mapping (dictionary).')

        if 'output' not in dumped_configuration or not isinstance(dumped_configuration['output'], str):
            raise ConfigurationError('The output directory path is required and must be a string.', contexts=['`output`'])
        with ensure_context('`output`'):
            output_directory_path = ensure_path(dumped_configuration['output'])

        if 'base_url' not in dumped_configuration or not isinstance(dumped_configuration['base_url'], str):
            raise ConfigurationError('The base URL is required and must be a string.', contexts=['`base_url`'])
        base_url = dumped_configuration['base_url']

        loaded_configuration = cls(output_directory_path, base_url)

        if 'title' in dumped_configuration:
            if not isinstance(dumped_configuration['title'], str):
                raise ConfigurationError('The title must be a string.', contexts=['`title`'])
            loaded_configuration.title = dumped_configuration['title']

        if 'author' in dumped_configuration:
            if not isinstance(dumped_configuration['author'], str):
                raise ConfigurationError('The author must be a string.', contexts=['`author`'])
            loaded_configuration.author = dumped_configuration['author']

        if 'root_path' in dumped_configuration:
            if not isinstance(dumped_configuration['root_path'], str):
                raise ConfigurationError('The root path must be a string.', contexts=['`root_path`'])
            loaded_configuration.root_path = dumped_configuration['root_path']

        if 'clean_urls' in dumped_configuration:
            if not isinstance(dumped_configuration['clean_urls'], bool):
                raise ConfigurationError('Clean URLs must be enabled (true) or disabled (false) with a boolean.', contexts=['`clean_urls`'])
            loaded_configuration.clean_urls = dumped_configuration['clean_urls']

        if 'content_negotiation' in dumped_configuration:
            if not isinstance(dumped_configuration['content_negotiation'], bool):
                raise ConfigurationError('Content negotiation must be enabled (true) or disabled (false) with a boolean.', contexts=['`content_negotiation`'])
            loaded_configuration.content_negotiation = dumped_configuration['content_negotiation']

        if 'debug' in dumped_configuration:
            if not isinstance(dumped_configuration['debug'], bool):
                raise ConfigurationError('Debugging must be enabled (true) or disabled (false) with a boolean.', contexts=['`debug`'])
            loaded_configuration.debug = dumped_configuration['debug']

        if 'assets' in dumped_configuration:
            if not isinstance(dumped_configuration['assets'], str):
                raise ConfigurationError('The assets directory path must be a string.', contexts=['`assets`'])
            with ensure_context('`assets`'):
                loaded_configuration.assets_directory_path = ensure_directory_path(dumped_configuration['assets'])

        if 'lifetime_threshold' in dumped_configuration:
            if not isinstance(dumped_configuration['lifetime_threshold'], int):
                raise ConfigurationError('The lifetime threshold must be an integer.', contexts=['`lifetime_threshold`'])
            loaded_configuration.lifetime_threshold = dumped_configuration['lifetime_threshold']

        if 'locales' in dumped_configuration:
            with ensure_context('`locales`'):
                loaded_configuration._locales = LocalesConfiguration.load(dumped_configuration['locales'])

        if 'extensions' in dumped_configuration:
            with ensure_context('`extensions`'):
                loaded_configuration._extensions = AppExtensionsConfiguration.load(dumped_configuration['extensions'])

        if 'theme' in dumped_configuration:
            with ensure_context('`theme`'):
                loaded_configuration._theme = ThemeConfiguration.load(dumped_configuration['theme'])

        return loaded_configuration

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


@reactive
class App(Configurable, Environment):
    def __init__(self, configuration: Configuration):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(configuration)
        self._active = False
        self._ancestry = Ancestry()
        self._assets = FileSystem()
        self._dispatcher = None
        self._localized_url_generator = AppUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._debug = None
        self._locale = None
        self._translations = defaultdict(NullTranslations)
        self._default_translations = None
        self._extensions = None
        self._activation_exit_stack = AsyncExitStack()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return Configuration

    async def wait(self) -> None:
        await self._wait_for_threads()

    async def _wait_for_threads(self) -> None:
        del self.executor

    async def activate(self) -> None:
        if self._active:
            raise RuntimeError('This application is active already.')
        self._active = True

        await self._wait_for_threads()

        try:
            await self._activation_exit_stack.enter_async_context(self.with_locale(self.locale))
            for extension in self.extensions.flatten():
                await extension.activate()
                self._activation_exit_stack.push_async_callback(extension.deactivate)
        except BaseException:
            await self.deactivate()
            raise

    async def deactivate(self):
        if not self._active:
            raise RuntimeError('This application is not yet active.')
        self._active = False

        await self._wait_for_threads()

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
        extension_types_enabled_in_configuration = {
            app_extension_configuration.extension_type
            for app_extension_configuration in self._configuration.extensions
            if app_extension_configuration.enabled
        }

        extension_types_sorter = TopologicalSorter(
            build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        extension_types_sorter.prepare()

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                if issubclass(extension_type, ConfigurableExtension):
                    if extension_type not in extension_types_enabled_in_configuration or self._configuration.extensions[extension_type].extension_configuration is None:
                        configuration = extension_type.default_configuration()
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
        if len(self._assets.paths) == 0:
            self._assets.paths.appendleft((ASSETS_DIRECTORY_PATH, 'utf-8'))
            for extension in self.extensions.flatten():
                if extension.assets_directory_path is not None:
                    self._assets.paths.appendleft((extension.assets_directory_path, 'utf-8'))
            if self._configuration.assets_directory_path:
                self._assets.paths.appendleft((self._configuration.assets_directory_path, None))

        return self._assets

    @assets.deleter
    def assets(self) -> None:
        self._assets.paths.clear()

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @reactive
    @property
    def translations(self) -> Dict[str, NullTranslations]:
        if len(self._translations) == 0:
            self._translations['en-US'] = NullTranslations()
            for locale_configuration in self._configuration.locales:
                for assets_path, _ in reversed(self._assets.paths):
                    translations = open_translations(locale_configuration.locale, assets_path)
                    if translations:
                        translations.add_fallback(self._translations[locale_configuration])
                        self._translations[locale_configuration] = translations

        return self._translations

    @translations.deleter
    def translations(self) -> None:
        self._translations.clear()

    @reactive
    @property
    def jinja2_environment(self) -> Jinja2Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import BettyEnvironment
            self._jinja2_environment = BettyEnvironment(self)

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
            self._executor = ExceptionRaisingExecutor(ThreadPoolExecutor())
        return self._executor

    @executor.deleter
    def executor(self) -> None:
        if self._executor is not None:
            self._executor.shutdown()
            self._executor = None

    @property
    def locks(self) -> Locks:
        return self._locks

    @reactive
    @property
    def http_client(self) -> aiohttp.ClientSession:
        if self._http_client is None:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
        return self._http_client

    @http_client.deleter
    def http_client(self) -> None:
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    @asynccontextmanager
    async def with_locale(self, locale: str) -> App:
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        locale = negotiate_locale(locale, [locale_configuration.locale for locale_configuration in self.configuration.locales])

        if locale is None:
            raise ValueError('Locale "%s" is not enabled.' % locale)

        previous_locale = self._locale
        if locale == previous_locale:
            yield self
            return
        await self._wait_for_threads()

        self._locale = locale
        with Translations(self.translations[locale]):
            self.react.getattr('locale').react.trigger()
            yield self
            await self._wait_for_threads()

        self._locale = previous_locale
        self.react.getattr('locale').react.trigger()

    @asynccontextmanager
    async def with_debug(self, debug: bool) -> App:
        previous_debug = self.debug
        if debug == previous_debug:
            yield self
            return
        await self._wait_for_threads()

        self._debug = debug
        self.react.getattr('debug').react.trigger()
        yield self
        await self._wait_for_threads()

        self._debug = previous_debug
        self.react.getattr('debug').react.trigger()
