import json
from collections import OrderedDict
from os import path
from typing import Dict, Optional, List, Callable, Type
from urllib.parse import urlparse

import yaml
from babel import parse_locale
from voluptuous import Schema, All, Required, Invalid, IsDir, Any, Range

from betty import _CACHE_DIRECTORY_PATH, os
from betty.error import UserFacingError, ContextError
from betty.extension import ConfigurableExtension, Configuration as ExtensionTypeConfiguration, Extension
from betty.react import reactive, ReactiveDict
from betty.voluptuous import Path, ExtensionType


class ConfigurationError(UserFacingError, ContextError, ValueError):
    pass


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

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def alias(self) -> str:
        if self._alias is None:
            return self.locale
        return self._alias


@reactive
class ExtensionConfiguration:
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, configuration: Optional[ExtensionTypeConfiguration] = None):
        self._extension_type = extension_type
        self._enabled = enabled
        if configuration is None and issubclass(extension_type, ConfigurableExtension):
            configuration = extension_type.default_configuration()
        if configuration is not None:
            configuration.react(self)
        self._extension_type_configuration = configuration

    def __repr__(self):
        return '<%s.%s(%s)>' % (self.__class__.__module__, self.__class__.__name__, self.extension_type)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.extension_type != other.extension_type:
            return False
        if self.enabled != other.enabled:
            return False
        if self.extension_type_configuration != other.extension_type_configuration:
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
    def extension_type_configuration(self) -> Optional[ExtensionTypeConfiguration]:
        return self._extension_type_configuration


def _extensions_configuration(extensions_configuration_dict: Optional[Dict[str, Any]] = None) -> Dict[Type[Extension], ExtensionConfiguration]:
    # Validate the extension type names, and import the types.
    extension_types_by_name = {}
    schemas = {}
    for extension_type_name in extensions_configuration_dict.keys():
        extension_type = ExtensionType()(extension_type_name)
        extension_types_by_name[extension_type_name] = extension_type
        schemas[extension_type_name] = _extension_configuration_schema(extension_type)

    typed_extensions_configuration_dict = Schema(schemas)(extensions_configuration_dict)

    # Return fully typed and coerced extension types and their configurations.
    return {
        extension_types_by_name[extension_type_name]: typed_extensions_configuration_dict[extension_type_name] for extension_type_name in extensions_configuration_dict.keys()
    }


def _extension_configuration_schema(extension_type: Type[Extension]):
    return All(
        Schema({
            Required('enabled', default=True): bool,
            Required('configuration', default=dict): _build_extension_type_configuration_schema(extension_type),
        }),
        lambda kwargs: ExtensionConfiguration(extension_type, **kwargs),
    )


def _build_extension_type_configuration_schema(extension_type: Type[Extension]):
    def _extension_type_configuration_schema(extension_configuration_dict: Optional[Dict[str, Any]]):
        if issubclass(extension_type, ConfigurableExtension):
            if extension_configuration_dict is None:
                return
            return extension_type.configuration_from_dict(extension_configuration_dict)
        elif extension_configuration_dict != {}:
            raise Invalid('Extension %s is not configurable, so its configuration must be empty.')

    return _extension_type_configuration_schema


@reactive
class ThemeConfiguration:
    def __init__(self):
        self._background_image_id = None

    @reactive
    @property
    def background_image_id(self) -> Optional[str]:
        return self._background_image_id

    @background_image_id.setter
    def background_image_id(self, background_image_id: Optional[str]) -> None:
        self._background_image_id = background_image_id


@reactive
class Configuration:
    def __init__(self, output_directory_path: str, base_url: str):
        self.cache_directory_path = _CACHE_DIRECTORY_PATH
        self.output_directory_path = output_directory_path
        self.base_url = base_url
        self.root_path = '/'
        self.clean_urls = False
        self.content_negotiation = False
        self.title = 'Betty'
        self.author = None
        self._extensions = ReactiveDict()
        self._extensions.react(self)
        self.mode = 'production'
        self.assets_directory_path = None
        default_locale = 'en-US'
        self._locales = ReactiveDict({
            default_locale: LocaleConfiguration(default_locale),
        })
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
    def www_directory_path(self) -> str:
        return path.join(self.output_directory_path, 'www')

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

    @property
    def locales(self) -> Dict[str, LocaleConfiguration]:
        return self._locales

    @property
    def default_locale(self) -> str:
        return next(iter(self.locales))

    @property
    def multilingual(self) -> bool:
        return len(self.locales) > 1

    @property
    def extensions(self) -> Dict[Type[Extension], ExtensionConfiguration]:
        return self._extensions

    @reactive
    @property
    def theme(self) -> ThemeConfiguration:
        return self._theme

    @reactive
    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str):
        self._mode = mode

    @reactive
    @property
    def lifetime_threshold(self) -> int:
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int):
        if lifetime_threshold < 1:
            raise ConfigurationError('The lifetime threshold must be a positive number.')
        self._lifetime_threshold = lifetime_threshold


def _locales_configuration(configuration: List):
    locales_configuration = OrderedDict()
    for locale_configuration in configuration:
        locale = locale_configuration['locale']
        parse_locale(locale, '-')
        locales_configuration[locale] = LocaleConfiguration(
            locale,
            locale_configuration['alias'] if 'alias' in locale_configuration else None,
        )
    return locales_configuration


def _theme_configuration(configuration_dict: Dict) -> ThemeConfiguration:
    theme_configuration = ThemeConfiguration()

    for key, value in configuration_dict.items():
        setattr(theme_configuration, key, value)

    return theme_configuration


def _configuration(configuration_dict: Dict) -> Configuration:
    configuration = Configuration(
        configuration_dict.pop('output'),
        configuration_dict.pop('base_url'),
    )

    if 'assets' in configuration_dict:
        configuration.assets_directory_path = configuration_dict['assets']
        del configuration_dict['assets']

    if 'extensions' in configuration_dict:
        configuration.extensions.update(configuration_dict['extensions'])
        del configuration_dict['extensions']

    if 'locales' in configuration_dict:
        # Replace the default locale with the explicitly configured locales.
        configuration.locales.clear()
        configuration.locales.update(configuration_dict['locales'])
        del configuration_dict['locales']

    if 'theme' in configuration_dict:
        configuration.theme.background_image_id = configuration_dict['theme'].background_image_id
        del configuration_dict['theme']

    for key, value in configuration_dict.items():
        setattr(configuration, key, value)

    return configuration


_ConfigurationSchema = Schema(All({
    Required('output'): All(str, Path()),
    'title': str,
    'author': str,
    'locales': All(list, _locales_configuration),
    Required('base_url'): str,
    'root_path': str,
    'clean_urls': bool,
    'content_negotiation': bool,
    'mode': Any('development', 'production'),
    'assets': All(str, IsDir(), Path()),
    'extensions': All(dict, _extensions_configuration),
    Required('theme', default=dict): All({
        'background_image_id': str,
    }, _theme_configuration),
    'lifetime_threshold': All(int, Range(min=0)),
}, _configuration))


def _from_dict(configuration_dict: Dict) -> Configuration:
    try:
        return _ConfigurationSchema(configuration_dict)
    except Invalid as e:
        raise ConfigurationError(e)


def from_json(configuration_json: str) -> Configuration:
    try:
        return _from_dict(json.loads(configuration_json))
    except json.JSONDecodeError as e:
        raise ConfigurationError('Invalid JSON: %s.' % e)


def from_yaml(configuration_yaml: str) -> Configuration:
    try:
        return _from_dict(yaml.safe_load(configuration_yaml))
    except yaml.YAMLError as e:
        raise ConfigurationError('Invalid YAML: %s' % e)


# These loaders must take a single argument, which is the configuration in their format, as a string. They must return
# Configuration, or raise ConfigurationError.
FORMAT_LOADERS: Dict[str, Callable[[str], Configuration]] = {
    '.json': from_json,
    '.yaml': from_yaml,
    '.yml': from_yaml,
}


def from_file(f) -> Configuration:
    file_base_name, file_extension = path.splitext(f.name)
    try:
        loader = FORMAT_LOADERS[file_extension]
    except KeyError:
        raise ConfigurationError('Unknown file format "%s". Supported formats are: %s.' % (
            file_extension, ', '.join(FORMAT_LOADERS.keys())))
    # Change the working directory to allow relative paths to be resolved against the configuration file's directory
    # path.
    with os.ChDir(path.dirname(f.name)):
        try:
            return loader(f.read())
        except ContextError as e:
            raise e.add_context('in %s' % path.abspath(f.name))


def _to_dict(configuration: Configuration) -> Dict:
    configuration_dict = {
        'output': configuration.output_directory_path,
        'base_url': configuration.base_url,
        'title': configuration.title,
    }
    if configuration.root_path is not None:
        configuration_dict['root_path'] = configuration.root_path
    if configuration.clean_urls is not None:
        configuration_dict['clean_urls'] = configuration.clean_urls
    if configuration.author is not None:
        configuration_dict['author'] = configuration.author
    if configuration.content_negotiation is not None:
        configuration_dict['content_negotiation'] = configuration.content_negotiation
    if configuration.mode is not None:
        configuration_dict['mode'] = configuration.mode
    if configuration.assets_directory_path is not None:
        configuration_dict['assets'] = configuration.assets_directory_path
    if len(configuration.locales) > 0:
        configuration_dict['locales'] = []
        for locale_configuration in configuration.locales.values():
            locale_configuration_dict = {
                'locale': locale_configuration.locale,
            }
            if locale_configuration.alias != locale_configuration.locale:
                locale_configuration_dict['alias'] = locale_configuration.alias
            configuration_dict['locales'].append(locale_configuration_dict)
    if len(configuration.extensions) > 0:
        configuration_dict['extensions'] = {}
        for extension_type, extension_configuration in configuration.extensions.items():
            if issubclass(extension_type, ConfigurableExtension):
                extension_type_configuration = extension_type.configuration_to_dict(extension_configuration.extension_type_configuration)
            else:
                extension_type_configuration = {}
            configuration_dict['extensions'][extension_type.name()] = {
                'enabled': extension_configuration.enabled,
                'configuration': extension_type_configuration,
            }
    if configuration.lifetime_threshold is not None:
        configuration_dict['lifetime_threshold'] = configuration.lifetime_threshold
    if configuration.theme.background_image_id is not None:
        configuration_dict.setdefault('theme', {})
        configuration_dict['theme']['background_image_id'] = configuration.theme.background_image_id

    return configuration_dict


def to_json(configuration: Configuration) -> str:
    return json.dumps(_to_dict(configuration))


def to_yaml(configuration: Configuration) -> str:
    return yaml.safe_dump(_to_dict(configuration))


# These dumpers must take a single argument, which is Configuration. They must return a single string.
FORMAT_DUMPERS: Dict[str, Callable[[Configuration], str]] = {
    '.json': to_json,
    '.yaml': to_yaml,
    '.yml': to_yaml,
}


def to_file(f, configuration: Configuration) -> None:
    file_base_name, file_extension = path.splitext(f.name)
    try:
        dumper = FORMAT_DUMPERS[file_extension]
    except KeyError:
        raise ValueError('Unknown file format "%s". Supported formats are: %s.' % (
            file_extension, ', '.join(FORMAT_DUMPERS.keys())))
    # Change the working directory to allow absolute paths to be turned relative to the configuration file's directory
    # path.
    with os.ChDir(path.dirname(f.name)):
        f.write(dumper(configuration))
