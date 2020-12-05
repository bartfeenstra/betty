import json
from collections import OrderedDict
from os import path
from typing import Dict, Optional, List, Callable, Type

import yaml
from babel import parse_locale
from voluptuous import Schema, All, Required, Invalid, IsDir, Any, Range

import betty
from betty import _CACHE_DIRECTORY_PATH, os
from betty.error import ContextError, UserFacingError
from betty.voluptuous import Path, Importable


class LocaleConfiguration:
    def __init__(self, locale: str, alias: str = None):
        self._locale = locale
        self._alias = alias

    def __repr__(self):
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.locale, self.alias)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self._locale != other._locale:
            return False
        if self._alias != other._alias:
            return False
        return True

    @property
    def locale(self) -> str:
        return self._locale

    @property
    def alias(self) -> str:
        if self._alias is None:
            return self._locale
        return self._alias


def _extensions_configuration_schema(extensions_configuration_dict: Optional[Dict[str, Any]] = None):
    from betty.extension import Extension

    # Validate the extension type names, and import the types.
    extension_types_by_name = {}
    for extension_type_name in extensions_configuration_dict.keys():
        extension_type = Importable()(extension_type_name)
        try:
            if not issubclass(extension_type, Extension):
                raise Invalid('"%s" is not a Betty extension.' % extension_type_name)
        except TypeError:
            raise Invalid('"%s" is not a Betty extension.' % extension_type_name)
        extension_types_by_name[extension_type_name] = extension_type

    # Validate each extension's configuration.
    schema = Schema({
        extension_type_name: extension_types_by_name[extension_type_name].configuration_schema for extension_type_name in extensions_configuration_dict.keys()
    })
    typed_extensions_configuration_dict = schema(extensions_configuration_dict)

    # Return fully typed and coerced extension types and their configurations.
    return {
        extension_types_by_name[extension_type_name]: typed_extensions_configuration_dict[extension_type_name] for extension_type_name in extensions_configuration_dict.keys()
    }


class ThemeConfiguration:
    background_image_id: Optional[str]

    def __init__(self):
        self.background_image_id = None


class Configuration:
    cache_directory_path: str
    content_negotiation: bool
    title: str
    mode: str
    locales: Dict[str, LocaleConfiguration]
    author: Optional[str]
    extensions: Dict[Type['betty.extension.Extension'], Any]
    assets_directory_path: Optional[str]
    theme: ThemeConfiguration
    lifetime_threshold: int

    def __init__(self, output_directory_path: str, base_url: str):
        self.cache_directory_path = _CACHE_DIRECTORY_PATH
        self.output_directory_path = output_directory_path
        self.base_url = base_url.rstrip(
            '/') if not base_url.endswith('://') else base_url
        self._root_path = '/'
        self._clean_urls = False
        self.content_negotiation = False
        self.title = 'Betty'
        self.author = None
        self.extensions = {}
        self.mode = 'production'
        self.assets_directory_path = None
        self.locales = OrderedDict()
        default_locale = 'en-US'
        self.locales[default_locale] = LocaleConfiguration(default_locale)
        self.theme = ThemeConfiguration()
        self.lifetime_threshold = 125

    @property
    def www_directory_path(self) -> str:
        return path.join(self.output_directory_path, 'www')

    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str):
        if not root_path.endswith('/'):
            root_path += '/'
        self._root_path = root_path

    @property
    def clean_urls(self) -> bool:
        return self._clean_urls or self.content_negotiation

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool):
        self._clean_urls = clean_urls

    @property
    def default_locale(self) -> str:
        return next(iter(self.locales))

    @property
    def multilingual(self) -> bool:
        return len(self.locales) > 1


def _locales_configuration(configuration: List):
    locales_configuration = OrderedDict()
    for locale_configuration in configuration:
        locale = locale_configuration['locale']
        parse_locale(locale, '-')
        locales_configuration[locale] = LocaleConfiguration(
            locale, locale_configuration['alias'] if 'alias' in locale_configuration else None)
    return locales_configuration


def _theme_configuration(configuration_dict: Dict) -> ThemeConfiguration:
    theme_configuration = ThemeConfiguration()

    for key, value in configuration_dict.items():
        setattr(theme_configuration, key, value)

    return theme_configuration


def _configuration(configuration_dict: Dict) -> Configuration:
    configuration = Configuration(
        configuration_dict.pop('output'), configuration_dict.pop('base_url'))

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
    'assets_directory_path': All(str, IsDir(), Path()),
    'extensions': All(dict, _extensions_configuration_schema),
    Required('theme', default=dict): All({
        'background_image_id': str,
    }, _theme_configuration),
    'lifetime_threshold': All(int, Range(min=1)),
}, _configuration))


class ConfigurationValueError(ContextError, UserFacingError, ValueError):
    pass  # pragma: no cover


def _from_dict(configuration_dict: Dict) -> Configuration:
    try:
        return _ConfigurationSchema(configuration_dict)
    except Invalid as e:
        raise ConfigurationValueError(e)


def from_json(configuration_json: str) -> Configuration:
    try:
        return _from_dict(json.loads(configuration_json))
    except json.JSONDecodeError as e:
        raise ConfigurationValueError('Invalid JSON: %s.' % e)


def from_yaml(configuration_yaml: str) -> Configuration:
    try:
        return _from_dict(yaml.safe_load(configuration_yaml))
    except yaml.YAMLError as e:
        raise ConfigurationValueError('Invalid YAML: %s' % e)


# These factories must take a single argument, which is the configuration in their format, as a string. They must return
# Configuration, or raise ConfigurationValueError.
_from_format_factories: Dict[str, Callable[[str], Configuration]] = {
    '.json': from_json,
    '.yaml': from_yaml,
    '.yml': from_yaml,
}


def from_file(f) -> Configuration:
    file_base_name, file_extension = path.splitext(f.name)
    try:
        factory = _from_format_factories[file_extension]
    except KeyError:
        raise ConfigurationValueError('Unknown file format "%s". Supported formats are: %s.' % (
            file_extension, ', '.join(_from_format_factories.keys())))
    # Change the working directory to allow relative paths to be resolved against the configuration file's directory
    # path.
    with os.ChDir(path.dirname(f.name)):
        try:
            return factory(f.read())
        except ConfigurationValueError as e:
            raise e.add_context('in %s' % path.abspath(f.name))
