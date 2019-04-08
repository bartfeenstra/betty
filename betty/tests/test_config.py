from json import dumps
from tempfile import TemporaryFile
from typing import Any, Dict, Type
from unittest import TestCase

from betty.config import from_file
from betty.plugin import Plugin


class InspectableConfigurationPlugin(Plugin):
    def __init__(self, configuration):
        self.configuration = configuration

    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls(configuration)


class FromTest(TestCase):
    _MINIMAL_CONFIG_DICT = {
        'inputGrampsFilePath': '/tmp/path/to/data.xml',
        'outputDirectoryPath': '/tmp/path/to/site',
        'url': 'https://example.com',
    }

    def _writes(self, config: str):
        f = TemporaryFile(mode='r+')
        f.write(config)
        f.seek(0)
        return f

    def _write(self, config_dict: Dict[str, Any]):
        return self._writes(dumps(config_dict))

    def test_from_file_should_parse_minimal(self):
        with self._write(self._MINIMAL_CONFIG_DICT) as f:
            configuration = from_file(f)
        self.assertEquals(
            self._MINIMAL_CONFIG_DICT['inputGrampsFilePath'], configuration.input_gramps_file_path)
        self.assertEquals(
            self._MINIMAL_CONFIG_DICT['outputDirectoryPath'], configuration.output_directory_path)
        self.assertEquals(self._MINIMAL_CONFIG_DICT['url'], configuration.url)
        self.assertEquals('Betty', configuration.title)

    def test_from_file_should_parse_title(self):
        title = 'My first Betty site'
        config_dict = self._MINIMAL_CONFIG_DICT.copy()
        config_dict['title'] = title
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(title, configuration.title)

    def test_from_file_should_error_if_invalid_json(self):
        with self._writes('') as f:
            with self.assertRaises(ValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_config(self):
        config_dict = {}
        with self._write(config_dict) as f:
            with self.assertRaises(ValueError):
                from_file(f)

    def test_without_plugins(self):
        with self._write(self._MINIMAL_CONFIG_DICT) as f:
            configuration = from_file(f)
        self.assertCountEqual([], configuration.plugins)

    @staticmethod
    def _plugin_name(cls: Type):
        return '%s.%s' % (cls.__module__, cls.__name__)

    def test_with_one_plugin(self):
        plugin_configuration = {
            'orange': 'juice',
        }
        config_dict = self._MINIMAL_CONFIG_DICT.copy()
        config_dict['plugins'] = {
            self._plugin_name(InspectableConfigurationPlugin): plugin_configuration,
        }
        with self._write(config_dict) as f:
            configuration = from_file(f)
        self.assertEquals(1, len(configuration.plugins))
        self.assertEquals(plugin_configuration, configuration.plugins[InspectableConfigurationPlugin])
