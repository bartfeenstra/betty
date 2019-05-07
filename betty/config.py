from importlib import import_module
from json import loads, load, JSONDecodeError
from os.path import join, abspath, dirname
from typing import Dict, Type, Optional

from jsonschema import validate, ValidationError


class Configuration:
    def __init__(self, output_directory_path: str, url: str):
        self._output_directory_path = output_directory_path
        self._url = url
        self._title = 'Betty'
        self._plugins = {}
        self._mode = 'production'
        self._resources_path = None

    @property
    def output_directory_path(self) -> str:
        return self._output_directory_path

    @property
    def url(self):
        return self._url

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
    def resources_path(self) -> Optional[str]:
        return self._resources_path

    @resources_path.setter
    def resources_path(self, resources_path: str) -> None:
        self._resources_path = resources_path


def _from_dict(config_dict: Dict) -> Configuration:
    configuration = Configuration(
        config_dict['outputDirectoryPath'], config_dict['url'])
    if 'title' in config_dict:
        configuration.title = config_dict['title']

    if 'mode' in config_dict:
        configuration.mode = config_dict['mode']

    if 'resources_path' in config_dict:
        configuration.resources_path = config_dict['resources_path']

    if 'plugins' in config_dict:
        def _normalize(plugin_definition):
            if isinstance(plugin_definition, str):
                return plugin_definition, {}
            plugin_definition.setdefault('configuration', {})
            return plugin_definition['type'], plugin_definition['configuration']

        for plugin_definition in config_dict['plugins']:
            plugin_type_name, plugin_configuration = _normalize(
                plugin_definition)
            plugin_module_name, plugin_class_name = plugin_type_name.rsplit(
                '.', 1)
            plugin_type = getattr(import_module(
                plugin_module_name), plugin_class_name)
            configuration.plugins[plugin_type] = plugin_configuration

    return configuration


def _from_json(config_json: str) -> Configuration:
    try:
        config_dict = loads(config_json)
    except JSONDecodeError:
        raise ValueError('Invalid JSON.')
    with open(join(dirname(abspath(__file__)), 'config.schema.json')) as f:
        try:
            validate(instance=config_dict, schema=load(f))
        except ValidationError:
            raise ValueError('The JSON is no valid Betty configuration.')
    return _from_dict(config_dict)


def from_file(f) -> Configuration:
    return _from_json(f.read())
