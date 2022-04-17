from __future__ import annotations
import weakref
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Type, Optional, Iterable, Any, Sequence, Dict, TYPE_CHECKING
from urllib.parse import urlparse

from babel.core import parse_locale, Locale
from reactives import reactive, scope
from reactives.factory.type import ReactiveInstance

from betty.app import Extension
from betty.config import Configurable, Configuration as GenericConfiguration, ConfigurationError, ensure_path, \
    ensure_directory_path
from betty.error import ensure_context
from betty.importlib import import_any
from betty.model.ancestry import Ancestry
from betty.os import PathLike


if TYPE_CHECKING:
    from betty.builtins import _


@reactive
class ProjectExtensionConfiguration(ReactiveInstance):
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

    @reactive  # type: ignore
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Optional[GenericConfiguration]:
        return self._extension_configuration


class ProjectExtensionsConfiguration(GenericConfiguration):
    def __init__(self, configurations: Optional[Iterable[ProjectExtensionConfiguration]] = None):
        super().__init__()
        self._configurations: Dict[Type[Extension], ProjectExtensionConfiguration] = OrderedDict()
        if configurations is not None:
            for configuration in configurations:
                self.add(configuration)

    @scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> ProjectExtensionConfiguration:
        return self._configurations[extension_type]

    def __delitem__(self, extension_type: Type[Extension]) -> None:
        self.remove(extension_type)

    @scope.register_self
    def __iter__(self) -> Iterable[ProjectExtensionConfiguration]:
        return (configuration for configuration in self._configurations.values())

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other):
        if not isinstance(other, ProjectExtensionsConfiguration):
            return NotImplemented
        return self._configurations == other._configurations

    def remove(self, *extension_types: Type[Extension]) -> None:
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].react.shutdown(self)
            del self._configurations[extension_type]
        self.react.trigger()

    def clear(self) -> None:
        self.remove(*self._configurations.keys())

    def add(self, *configurations: ProjectExtensionConfiguration) -> None:
        for configuration in configurations:
            self._configurations[configuration.extension_type] = configuration
            configuration.react(self)
        self.react.trigger()

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('App extensions configuration must be a mapping (dictionary).'))

        self.clear()

        for extension_type_name in dumped_configuration:
            with ensure_context(f'`{extension_type_name}`'):
                try:
                    extension_type = import_any(extension_type_name)
                except ImportError as e:
                    raise ConfigurationError(e)

                if not issubclass(extension_type, Extension):
                    raise ConfigurationError(_('"{extension_type_name}" is not a Betty extension.').format(extension_type_name=extension_type_name))

                dumped_extension_configuration = dumped_configuration[extension_type_name]

                if not isinstance(dumped_extension_configuration, dict):
                    raise ConfigurationError(_('The configuration must be a mapping (dictionary).'))

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

                self.add(ProjectExtensionConfiguration(
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
    def __init__(self, locale: str, alias: Optional[str] = None):
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
        self._configurations: OrderedDict[str, LocaleConfiguration] = OrderedDict()
        self.replace(configurations)

    @scope.register_self
    def __getitem__(self, locale: str) -> LocaleConfiguration:
        return self._configurations[locale]

    def __delitem__(self, locale: str) -> None:
        if len(self._configurations) <= 1:
            raise ConfigurationError(_('Cannot remove the last remaining locale {locale}').format(locale=Locale.parse(locale, '-').get_display_name()))
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

    @reactive  # type: ignore
    @property
    def default_locale(self) -> LocaleConfiguration:
        return next(iter(self._configurations.values()))

    @default_locale.setter
    def default_locale(self, configuration: LocaleConfiguration) -> None:
        self._configurations[configuration.locale] = configuration
        self._configurations.move_to_end(configuration.locale, False)
        self.react.trigger()

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, list):
            raise ConfigurationError(_('Locales configuration much be a list.'))

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

    @reactive  # type: ignore
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
        self._extensions = ProjectExtensionsConfiguration()
        self._extensions.react(self)
        self._debug = False
        self.assets_directory_path = None
        self._locales = LocalesConfiguration()
        self._locales.react(self)
        self._theme = ThemeConfiguration()
        self._theme.react(self)
        self.lifetime_threshold = 125

    @reactive  # type: ignore
    @property
    def output_directory_path(self) -> Path:
        return self._output_directory_path

    @output_directory_path.setter
    def output_directory_path(self, output_directory_path: PathLike) -> None:
        self._output_directory_path = Path(output_directory_path)

    @reactive  # type: ignore
    @property
    def assets_directory_path(self) -> Optional[str]:
        return self._assets_directory_path

    @assets_directory_path.setter
    def assets_directory_path(self, assets_directory_path: Optional[str]) -> None:
        self._assets_directory_path = assets_directory_path

    @reactive  # type: ignore
    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @reactive  # type: ignore
    @property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: Optional[str]) -> None:
        self._author = author

    @property
    def www_directory_path(self) -> Path:
        return self.output_directory_path / 'www'

    @reactive  # type: ignore
    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str):
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise ConfigurationError(_('The base URL must start with a scheme such as https://, http://, or file://.'))
        if not base_url_parts.netloc:
            raise ConfigurationError(_('The base URL must include a path.'))
        self._base_url = '%s://%s' % (base_url_parts.scheme, base_url_parts.netloc)

    @reactive  # type: ignore
    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str):
        self._root_path = root_path.strip('/')

    @reactive  # type: ignore
    @property
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    @content_negotiation.setter
    def content_negotiation(self, content_negotiation: bool):
        self._content_negotiation = content_negotiation

    @reactive  # type: ignore
    @property
    def clean_urls(self) -> bool:
        return self._clean_urls or self.content_negotiation

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool):
        self._clean_urls = clean_urls

    @reactive  # type: ignore
    @property
    def locales(self) -> LocalesConfiguration:
        return self._locales

    @property
    def multilingual(self) -> bool:
        return len(self.locales) > 1

    @property
    def extensions(self) -> ProjectExtensionsConfiguration:
        return self._extensions

    @reactive  # type: ignore
    @property
    def theme(self) -> ThemeConfiguration:
        return self._theme

    @reactive  # type: ignore
    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug

    @reactive  # type: ignore
    @property
    def lifetime_threshold(self) -> int:
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int):
        if lifetime_threshold < 1:
            raise ConfigurationError(_('The lifetime threshold must be a positive number.'))
        self._lifetime_threshold = lifetime_threshold

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('Betty configuration must be a mapping (dictionary).'))

        if 'output' not in dumped_configuration or not isinstance(dumped_configuration['output'], str):
            raise ConfigurationError(_('The output directory path is required and must be a string.'), contexts=['`output`'])
        with ensure_context('`output`'):
            self.output_directory_path = ensure_path(dumped_configuration['output'])

        if 'base_url' not in dumped_configuration or not isinstance(dumped_configuration['base_url'], str):
            raise ConfigurationError(_('The base URL is required and must be a string.'), contexts=['`base_url`'])
        self.base_url = dumped_configuration['base_url']

        if 'title' in dumped_configuration:
            if not isinstance(dumped_configuration['title'], str):
                raise ConfigurationError(_('The title must be a string.'), contexts=['`title`'])
            self.title = dumped_configuration['title']

        if 'author' in dumped_configuration:
            if not isinstance(dumped_configuration['author'], str):
                raise ConfigurationError(_('The author must be a string.'), contexts=['`author`'])
            self.author = dumped_configuration['author']

        if 'root_path' in dumped_configuration:
            if not isinstance(dumped_configuration['root_path'], str):
                raise ConfigurationError(_('The root path must be a string.'), contexts=['`root_path`'])
            self.root_path = dumped_configuration['root_path']

        if 'clean_urls' in dumped_configuration:
            if not isinstance(dumped_configuration['clean_urls'], bool):
                raise ConfigurationError(_('Clean URLs must be enabled (true) or disabled (false) with a boolean.'), contexts=['`clean_urls`'])
            self.clean_urls = dumped_configuration['clean_urls']

        if 'content_negotiation' in dumped_configuration:
            if not isinstance(dumped_configuration['content_negotiation'], bool):
                raise ConfigurationError(_('Content negotiation must be enabled (true) or disabled (false) with a boolean.'), contexts=['`content_negotiation`'])
            self.content_negotiation = dumped_configuration['content_negotiation']

        if 'debug' in dumped_configuration:
            if not isinstance(dumped_configuration['debug'], bool):
                raise ConfigurationError(_('Debugging must be enabled (true) or disabled (false) with a boolean.'), contexts=['`debug`'])
            self.debug = dumped_configuration['debug']

        if 'assets' in dumped_configuration:
            if not isinstance(dumped_configuration['assets'], str):
                raise ConfigurationError(_('The assets directory path must be a string.'), contexts=['`assets`'])
            with ensure_context('`assets`'):
                self.assets_directory_path = ensure_directory_path(dumped_configuration['assets'])

        if 'lifetime_threshold' in dumped_configuration:
            if not isinstance(dumped_configuration['lifetime_threshold'], int):
                raise ConfigurationError(_('The lifetime threshold must be an integer.'), contexts=['`lifetime_threshold`'])
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


class Project(Configurable[Configuration]):
    def __init__(self):
        super().__init__()

        self._ancestry = Ancestry()

    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return Configuration

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry
