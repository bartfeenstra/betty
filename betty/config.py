import json
from collections import OrderedDict
from importlib import import_module
from os import getcwd, path
from os.path import join, abspath, dirname
from typing import Dict, Type, Optional

import yaml
from voluptuous import Schema, All, Required, Invalid, IsDir, Any

from betty.error import ExternalContextError
from betty.locale import validate_locale
from betty.voluptuous import MapDict


class LocaleConfiguration:
    def __init__(self, locale: str, alias: str = None):
        self._locale = locale
        self._alias = alias

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


class Configuration:
    def __init__(self, output_directory_path: str, base_url: str):
        self._site_directory_path = getcwd()
        self._cache_directory_path = join(path.expanduser('~'), '.betty')
        self._output_directory_path = output_directory_path
        self._base_url = base_url.rstrip(
            '/') if not base_url.endswith('://') else base_url
        self._root_path = '/'
        self._clean_urls = False
        self._content_negotiation = False
        self._title = 'Betty'
        self._author = None
        self._plugins = {}
        self._mode = 'production'
        self._resources_directory_path = None
        self._locales = OrderedDict()
        default_locale = 'en-US'
        self._locales[default_locale] = LocaleConfiguration(default_locale)

    @property
    def site_directory_path(self) -> str:
        return self._site_directory_path

    @site_directory_path.setter
    def site_directory_path(self, site_directory_path: str) -> None:
        self._site_directory_path = abspath(site_directory_path)

    @property
    def cache_directory_path(self) -> str:
        return self._cache_directory_path

    @cache_directory_path.setter
    def cache_directory_path(self, cache_directory_path: str) -> None:
        self._cache_directory_path = cache_directory_path

    @property
    def output_directory_path(self) -> str:
        return abspath(join(self._site_directory_path, self._output_directory_path))

    @property
    def www_directory_path(self) -> str:
        return join(self.output_directory_path, 'www')

    @property
    def base_url(self) -> str:
        return self._base_url

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
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    @content_negotiation.setter
    def content_negotiation(self, content_negotiation: bool):
        self._content_negotiation = content_negotiation

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: str) -> None:
        self._author = author

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str) -> None:
        self._mode = mode

    @property
    def plugins(self) -> Dict[Type['Plugin'], Dict]:
        return self._plugins

    @property
    def resources_directory_path(self) -> Optional[str]:
        return abspath(join(self._site_directory_path, self._resources_directory_path)) if self._resources_directory_path else None

    @resources_directory_path.setter
    def resources_directory_path(self, resources_directory_path: str) -> None:
        self._resources_directory_path = resources_directory_path

    @property
    def locales(self) -> Dict[str, LocaleConfiguration]:
        return self._locales

    @property
    def default_locale(self) -> str:
        return next(iter(self._locales))

    @property
    def multilingual(self) -> bool:
        return len(self._locales) > 1


ConfigurationSchema = Schema({
    Required('output'): All(str),
    'title': All(str),
    'author': str,
    'locales': All(list, [{
        Required('locale'): validate_locale,
        Required('alias', default=None): Any(str, None),
    }]),
    Required('base_url'): All(str),
    'root_path': All(str),
    'clean_urls': All(bool),
    'content_negotiation': bool,
    'mode': Any('development', 'production'),
    'resources': All(str, IsDir()),
    'plugins': MapDict(str, dict),
})


class ConfigurationError(ExternalContextError):
    pass


def validate_configuration(schema: Schema, configuration: Any) -> Any:
    try:
        return schema(configuration)
    except Invalid as e:
        raise ConfigurationError(e)


def _from_dict(site_directory_path: str, config_dict: Dict) -> Configuration:
    config_dict = validate_configuration(ConfigurationSchema, config_dict)
    configuration = Configuration(
        config_dict['output'], config_dict['base_url'])
    configuration.site_directory_path = site_directory_path

    if 'title' in config_dict:
        configuration.title = config_dict['title']

    if 'author' in config_dict:
        configuration.author = config_dict['author']

    if 'locales' in config_dict:
        configuration.locales.clear()
        for locale_config in config_dict['locales']:
            locale = locale_config['locale']
            configuration.locales[locale] = LocaleConfiguration(
                locale, locale_config['alias'])

    if 'root_path' in config_dict:
        configuration.root_path = config_dict['root_path']

    if 'clean_urls' in config_dict:
        configuration.clean_urls = config_dict['clean_urls']

    if 'content_negotiation' in config_dict:
        configuration.content_negotiation = config_dict['content_negotiation']

    if 'mode' in config_dict:
        configuration.mode = config_dict['mode']

    if 'resources' in config_dict:
        configuration.resources_directory_path = config_dict['resources']

    if 'plugins' in config_dict:
        for plugin_type_name, plugin_configuration in config_dict['plugins'].items():
            plugin_module_name, plugin_class_name = plugin_type_name.rsplit(
                '.', 1)
            plugin_type = getattr(import_module(
                plugin_module_name), plugin_class_name)
            configuration.plugins[plugin_type] = plugin_configuration

    return configuration


def _from_json(site_directory_path: str, config_json: str) -> Configuration:
    try:
        config_dict = json.loads(config_json)
    except json.JSONDecodeError as e:
        raise ConfigurationError('Invalid JSON: %s.' % e)
    return _from_dict(site_directory_path, config_dict)


def _from_yaml(site_directory_path: str, config_yaml: str) -> Configuration:
    try:
        config_dict = yaml.safe_load(config_yaml)
    except yaml.YAMLError as e:
        raise ConfigurationError('Invalid YAML: %s' % e)
    return _from_dict(site_directory_path, config_dict)


_factories = {
    '.json': _from_json,
    '.yaml': _from_yaml,
    '.yml': _from_yaml,
}


def from_file(f) -> Configuration:
    file_base_name, file_extension = path.splitext(f.name)
    try:
        factory = _factories[file_extension]
    except KeyError:
        raise ConfigurationError('Unknown file format "%s". Supported formats are: %s.' % (
            file_extension, ', '.join(_factories.keys())))
    try:
        return factory(dirname(f.name), f.read())
    except ConfigurationError as e:
        raise e.add_context('In %s.' % abspath(f.name))
