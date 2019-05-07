from json import dumps
from os import getcwd
from tempfile import NamedTemporaryFile
from typing import Any, Dict
from unittest import TestCase

from parameterized import parameterized

from betty.config import from_file, Configuration
from betty.plugin import Plugin


class ConfigurationTest(TestCase):
    def test_working_directory_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')

        self.assertEquals(getcwd(), sut.working_directory_path)

        working_directory_path = '/tmp/betty-working-directory'
        sut.working_directory_path = working_directory_path
        self.assertEquals(working_directory_path, sut.working_directory_path)

    def test_resources_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')

        self.assertIsNone(sut.resources_path)

        absolute_resources_directory_path = '/tmp/betty-resources'
        sut.working_directory_path = absolute_resources_directory_path
        self.assertEquals(absolute_resources_directory_path, sut.working_directory_path)

        working_directory_path = '/tmp/betty-working-directory'
        sut.working_directory_path = working_directory_path
        relative_resources_directory_path = './betty-resources'
        sut.resources_path = relative_resources_directory_path
        self.assertEquals('/tmp/betty-working-directory/betty-resources', sut.resources_path)


class FromTest(TestCase):
    _MINIMAL_CONFIG_DICT = {
        'outputDirectoryPath': '/tmp/path/to/site',
        'url': 'https://example.com',
    }

    def _writes(self, config: str):
        f = NamedTemporaryFile(mode='r+')
        f.write(config)
        f.seek(0)
        return f

    def _write(self, config_dict: Dict[str, Any]):
        return self._writes(dumps(config_dict))

    def test_from_file_should_parse_minimal(self):
        with self._write(self._MINIMAL_CONFIG_DICT) as f:
            configuration = from_file(f)
        self.assertEquals(
            self._MINIMAL_CONFIG_DICT['outputDirectoryPath'], configuration.output_directory_path)
        self.assertEquals(self._MINIMAL_CONFIG_DICT['url'], configuration.url)
        self.assertEquals('Betty', configuration.title)
        self.assertEquals('production', configuration.mode)

    def test_from_file_should_parse_title(self):
        title = 'My first Betty site'
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['title'] = title
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(title, configuration.title)

    @parameterized.expand([
        ('production',),
        ('development',),
    ])
    def test_from_file_should_parse_mode(self, mode: str):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['mode'] = mode
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(mode, configuration.mode)

    def test_from_file_should_parse_resources_path(self):
        resources_path = '/tmp/betty'
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['resourcesPath'] = resources_path
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(resources_path, configuration.resources_path)

    def test_from_file_should_parse_one_plugin_shorthand(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = [Plugin.name()]
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: {},
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_parse_one_plugin(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = [{
            'type': Plugin.name(),
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
            'type': Plugin.name(),
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
