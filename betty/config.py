from importlib import import_module
from json import loads, load, JSONDecodeError
from os import getcwd
from os.path import join, abspath, dirname, expanduser
from typing import Dict, Type, Optional

from jsonschema import validate, ValidationError


class Configuration:
    def __init__(self, output_directory_path: str, base_url: str):
        self._site_directory_path = getcwd()
        self._cache_directory_path = join(expanduser('~'), '.betty')
        self._output_directory_path = output_directory_path
        self._base_url = base_url.rstrip('/') if not base_url.endswith('://') else base_url
        self._root_path = '/'
        self._clean_urls = False
        self._title = 'Betty'
        self._plugins = {}
        self._mode = 'production'
        self._resources_directory_path = None

    @property
    def site_directory_path(self) -> str:
        return self._site_directory_path

    @site_directory_path.setter
    def site_directory_path(self, site_directory_path: str) -> None:
        self._site_directory_path = abspath(site_directory_path)

    @property
    def cache_directory_path(self) -> str:
        return self._cache_directory_path

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
        root_path = root_path.rstrip('/')
        self._root_path = '/' + root_path if not root_path.startswith('/') else root_path

    @property
    def clean_urls(self) -> bool:
        return self._clean_urls

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool):
        self._clean_urls = clean_urls

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str) -> None:
        self._mode = mode

    @property
    def plugins(self) -> Dict[Type, Dict]:
        return self._plugins

    @property
    def resources_directory_path(self) -> Optional[str]:
        return abspath(join(self._site_directory_path, self._resources_directory_path)) if self._resources_directory_path else None

    @resources_directory_path.setter
    def resources_directory_path(self, resources_directory_path: str) -> None:
        self._resources_directory_path = resources_directory_path


def _from_dict(site_directory_path: str, config_dict: Dict) -> Configuration:
    configuration = Configuration(
        config_dict['output'], config_dict['base_url'])
    configuration.site_directory_path = site_directory_path

    if 'title' in config_dict:
        configuration.title = config_dict['title']

    if 'root_path' in config_dict:
        configuration.root_path = config_dict['root_path']

    if 'clean_urls' in config_dict:
        configuration.clean_urls = config_dict['clean_urls']

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
        config_dict = loads(config_json)
    except JSONDecodeError:
        raise ValueError('Invalid JSON.')
    with open(join(dirname(abspath(__file__)), 'config.schema.json')) as f:
        try:
            validate(instance=config_dict, schema=load(f))
        except ValidationError:
            raise ValueError('The JSON is no valid Betty configuration.')
    return _from_dict(site_directory_path, config_dict)


def from_file(f) -> Configuration:
    return _from_json(dirname(f.name), f.read())
