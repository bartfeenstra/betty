from json import loads, load, JSONDecodeError
from os.path import join
from typing import Dict

from jsonschema import validate, ValidationError

import betty


class Configuration:
    def __init__(self, input_gramps_file_path: str, output_directory_path: str, url: str):
        self._input_gramps_file_path = input_gramps_file_path
        self._output_directory_path = output_directory_path
        self._url = url
        self._title = 'Betty'

    @property
    def input_gramps_file_path(self) -> str:
        return self._input_gramps_file_path

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


def _from_dict(config_dict: Dict) -> Configuration:
    configuration = Configuration(config_dict['inputGrampsFilePath'], config_dict['outputDirectoryPath'],
                                  config_dict['url'])
    if 'title' in config_dict:
        configuration.title = config_dict['title']

    return configuration


def _from_json(config_json: str) -> Configuration:
    try:
        config_dict = loads(config_json)
    except JSONDecodeError:
        raise ValueError('Invalid JSON.')
    with open(join(betty.RESOURCE_PATH, 'config.schema.json')) as f:
        try:
            validate(instance=config_dict, schema=load(f))
        except ValidationError:
            raise ValueError('The JSON is no valid Betty configuration.')
    return _from_dict(config_dict)


def from_file(f) -> Configuration:
    return _from_json(f.read())
