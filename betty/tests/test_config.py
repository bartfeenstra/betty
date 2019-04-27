from json import dumps
from tempfile import TemporaryFile
from typing import Any, Dict, Type
from unittest import TestCase

from betty.config import from_file
from betty.plugin import Plugin


def _plugin_name(cls: Type):
    return '%s.%s' % (cls.__module__, cls.__name__)


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
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['title'] = title
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(title, configuration.title)

    def test_from_file_should_parse_one_plugin_shorthand(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = [_plugin_name(Plugin)]
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: {},
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_parse_one_plugin(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = [{
            'type': _plugin_name(Plugin),
        }]
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: {},
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_parse_one_plugin_with_configuration(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        plugin_configuration = {
            'check': 1337,
        }
        config_dict['plugins'] = [{
            'type': _plugin_name(Plugin),
            'configuration': plugin_configuration,
        }]
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: plugin_configuration,
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_error_if_unknown_plugin_type_module(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = ['foo.bar.Baz']
        with self._write(config_dict) as f:
            with self.assertRaises(ImportError):
                from_file(f)

    def test_from_file_should_error_if_unknown_plugin_type(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = ['%s.Foo' % self.__module__]
        with self._write(config_dict) as f:
            with self.assertRaises(AttributeError):
                from_file(f)

    def test_from_file_should_error_if_invalid_json(self):
        with self._writes('') as f:
            with self.assertRaises(ValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_config(self):
        config_dict = {}
        with self._write(config_dict) as f:
            with self.assertRaises(ValueError):
                from_file(f)
