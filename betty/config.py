import json
from collections import OrderedDict
from os import path
from typing import Dict, Type, Optional, List, Callable

import yaml
from babel import parse_locale
from voluptuous import Schema, All, Required, Invalid, IsDir, Any, Range

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


class PluginsConfiguration:
    def __init__(self, plugins_configuration: Dict[Type['Plugin'], Optional[Any]] = None):
        self._plugins_configuration = {}
        if plugins_configuration is not None:
            for plugin_type, plugin_configuration in plugins_configuration.items():
                self[plugin_type] = plugin_configuration

    def __setitem__(self, plugin_type: Type['Plugin'], plugin_configuration: Optional[Any] = None):
        try:
            self._plugins_configuration[plugin_type] = plugin_type.configuration_schema(plugin_configuration)
        except Invalid as e:
            raise ConfigurationValueError(e)

    def __getitem__(self, item):
        return self._plugins_configuration[item]

    def __contains__(self, item):
        return item in self._plugins_configuration

    def __iter__(self):
        yield from self._plugins_configuration.items()

    def __len__(self):
        return len(self._plugins_configuration)


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
    plugins: PluginsConfiguration
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
        self.plugins = PluginsConfiguration()
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


def _theme_configuration(config_dict: Dict) -> ThemeConfiguration:
    theme_configuration = ThemeConfiguration()

    for key, value in config_dict.items():
        setattr(theme_configuration, key, value)

    return theme_configuration


def _configuration(config_dict: Dict) -> Configuration:
    configuration = Configuration(
        config_dict.pop('output'), config_dict.pop('base_url'))

    for key, value in config_dict.items():
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
    'plugins': All(dict, lambda x: PluginsConfiguration({Importable()(plugin_type_name): plugin_configuration for plugin_type_name, plugin_configuration in x.items()})),
    Required('theme', default=dict): All({
        'background_image_id': str,
    }, _theme_configuration),
    'lifetime_threshold': All(int, Range(min=1)),
}, _configuration))


class ConfigurationValueError(ContextError, UserFacingError, ValueError):
    pass  # pragma: no cover


def _from_voluptuous(config_builtin: Any) -> Configuration:
    try:
        return _ConfigurationSchema(config_builtin)
    except Invalid as e:
        raise ConfigurationValueError(e)


def _from_json(config_json: str) -> Configuration:
    try:
        return _from_voluptuous(json.loads(config_json))
    except json.JSONDecodeError as e:
        raise ConfigurationValueError('Invalid JSON: %s.' % e)


def _from_yaml(config_yaml: str) -> Configuration:
    try:
        return _from_voluptuous(yaml.safe_load(config_yaml))
    except yaml.YAMLError as e:
        raise ConfigurationValueError('Invalid YAML: %s' % e)


# These factories must take a single argument, which is the configuration in their format, as a string. They must return
# Configuration, or raise ConfigurationValueError.
_from_format_factories: Dict[str, Callable[[str], Configuration]] = {
    '.json': _from_json,
    '.yaml': _from_yaml,
    '.yml': _from_yaml,
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
