from json import dumps
from os import getcwd
from os.path import join
from tempfile import NamedTemporaryFile
from typing import Any, Dict
from unittest import TestCase

from parameterized import parameterized

from betty.config import from_file, Configuration
from betty.plugin import Plugin


class ConfigurationTest(TestCase):
    def test_site_directory_path_with_cwd(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        self.assertEquals(getcwd(), sut.site_directory_path)

    def test_site_directory_path_with_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        site_directory_path = '/tmp/betty-working-directory'
        sut.site_directory_path = site_directory_path
        self.assertEquals(site_directory_path, sut.site_directory_path)

    def test_output_directory_path_with_absolute_path(self):
        output_directory_path = '/tmp/betty'
        sut = Configuration(output_directory_path, 'https://example.com')
        self.assertEquals(output_directory_path, sut.output_directory_path)

    def test_output_directory_path_with_relative_path(self):
        output_directory_path = './betty'
        sut = Configuration(output_directory_path, 'https://example.com')
        site_directory_path = '/tmp/betty-working-directory'
        sut.site_directory_path = site_directory_path
        self.assertEquals('/tmp/betty-working-directory/betty',
                          sut.output_directory_path)

    def test_www_directory_path_with_absolute_path(self):
        output_directory_path = '/tmp/betty'
        sut = Configuration(output_directory_path, 'https://example.com')
        expected = join(output_directory_path, 'www')
        self.assertEquals(expected, sut.www_directory_path)

    def test_resources_directory_path_without_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        self.assertIsNone(sut.resources_directory_path)

    def test_resources_directory_path_with_absolute_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        resources_directory_path = '/tmp/betty-resources'
        sut.resources_directory_path = resources_directory_path
        self.assertEquals(resources_directory_path,
                          sut.resources_directory_path)

    def test_resources_directory_path_with_relative_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        site_directory_path = '/tmp/betty-working-directory'
        sut.site_directory_path = site_directory_path
        resources_directory_path = './betty-resources'
        sut.resources_directory_path = resources_directory_path
        self.assertEquals(
            '/tmp/betty-working-directory/betty-resources', sut.resources_directory_path)

    def test_root_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        root_path = '/betty'
        sut.root_path = root_path
        self.assertEquals(root_path, sut.root_path)

    def test_clean_urls(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        clean_urls = True
        sut.clean_urls = clean_urls
        self.assertEquals(clean_urls, sut.clean_urls)


class FromTest(TestCase):
    _MINIMAL_CONFIG_DICT = {
        'output': '/tmp/path/to/site',
        'base_url': 'https://example.com',
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
            self._MINIMAL_CONFIG_DICT['output'], configuration.output_directory_path)
        self.assertEquals(
            self._MINIMAL_CONFIG_DICT['base_url'], configuration.base_url)
        self.assertEquals('Betty', configuration.title)
        self.assertEquals('production', configuration.mode)
        self.assertEquals('/', configuration.root_path)
        self.assertFalse(configuration.clean_urls)

    def test_from_file_should_parse_title(self):
        title = 'My first Betty site'
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['title'] = title
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(title, configuration.title)

    def test_from_file_should_root_path(self):
        root_path = '/betty'
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['root_path'] = root_path
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(root_path, configuration.root_path)

    def test_from_file_should_clean_urls(self):
        clean_urls = True
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['clean_urls'] = clean_urls
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(clean_urls, configuration.clean_urls)

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

    def test_from_file_should_parse_resources_directory_path(self):
        resources_directory_path = '/tmp/betty'
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['resources'] = resources_directory_path
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(resources_directory_path,
                              configuration.resources_directory_path)

    def test_from_file_should_parse_one_plugin_with_configuration(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        plugin_configuration = {
            'check': 1337,
        }
        config_dict['plugins'] = {
            Plugin.name(): plugin_configuration,
        }
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: plugin_configuration,
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_parse_one_plugin_without_configuration(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = {
            Plugin.name(): {},
        }
        with self._write(config_dict) as f:
            configuration = from_file(f)
            expected = {
                Plugin: {},
            }
            self.assertEquals(expected, configuration.plugins)

    def test_from_file_should_error_if_unknown_plugin_type_module(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = {
            'foo.bar.Baz': {},
        }
        with self._write(config_dict) as f:
            with self.assertRaises(ImportError):
                from_file(f)

    def test_from_file_should_error_if_unknown_plugin_type(self):
        config_dict = dict(**self._MINIMAL_CONFIG_DICT)
        config_dict['plugins'] = {
            '%s.Foo' % self.__module__: {},
        }
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
