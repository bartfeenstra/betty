from importlib import import_module
from json import loads, load, JSONDecodeError
from os import getcwd
from os.path import join, abspath, dirname
from typing import Dict, Type, Optional

from jsonschema import validate, ValidationError


class Configuration:
    def __init__(self, output_directory_path: str, url: str):
        self._working_directory_path = getcwd()
        self._output_directory_path = output_directory_path
        self._url = url
        self._title = 'Betty'
        self._plugins = {}
        self._mode = 'production'
        self._resources_directory_path = None

    @property
    def working_directory_path(self) -> str:
        return self._working_directory_path

    @working_directory_path.setter
    def working_directory_path(self, working_directory_path: str) -> None:
        self._working_directory_path = working_directory_path

    @property
    def output_directory_path(self) -> str:
        return self._abspath(self._output_directory_path)

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
    def resources_directory_path(self) -> Optional[str]:
        return self._abspath(self._resources_directory_path) if self._resources_directory_path else None

    @resources_directory_path.setter
    def resources_directory_path(self, resources_directory_path: str) -> None:
        self._resources_directory_path = resources_directory_path

    def _abspath(self, path: str):
        return abspath(join(self._working_directory_path, path))


def _from_dict(working_directory_path: str, config_dict: Dict) -> Configuration:
    configuration = Configuration(
        config_dict['output'], config_dict['url'])
    configuration.working_directory_path = working_directory_path

    if 'title' in config_dict:
        configuration.title = config_dict['title']

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


def _from_json(working_directory_path: str, config_json: str) -> Configuration:
    try:
        config_dict = loads(config_json)
    except JSONDecodeError:
        raise ValueError('Invalid JSON.')
    with open(join(dirname(abspath(__file__)), 'config.schema.json')) as f:
        try:
            validate(instance=config_dict, schema=load(f))
        except ValidationError:
            raise ValueError('The JSON is no valid Betty configuration.')
    return _from_dict(working_directory_path, config_dict)


def from_file(f) -> Configuration:
    return _from_json(dirname(f.name), f.read())
