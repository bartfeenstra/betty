import json
from collections import OrderedDict
from contextlib import contextmanager
from os.path import join
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict

import yaml
from parameterized import parameterized
from voluptuous import Schema, Required

from betty.config import from_file, Configuration, ConfigurationValueError, LocaleConfiguration, PluginsConfiguration
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.site import Site
from betty.tests import TestCase


class NonConfigurablePlugin(Plugin):
    pass  # pragma: no cover


class ConfigurablePlugin(Plugin):
    configuration_schema: Schema = Schema({
        Required('check'): lambda x: x
    })

    def __init__(self, check):
        self.check = check

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(configuration['check'])


class PluginsConfigurationTest(TestCase):
    def test_init_from_dict_with_valid_configuration_should_set(self):
        plugin_configuration = {
            'check': 1337,
        }
        plugins_configuration_dict = {
            ConfigurablePlugin: plugin_configuration,
        }
        sut = PluginsConfiguration(plugins_configuration_dict)
        self.assertEqual(plugin_configuration, sut[ConfigurablePlugin])

    def test_init_from_dict_with_invalid_configuration_should_raise_configuration_error(self):
        plugin_configuration = 1337
        plugins_configuration_dict = {
            ConfigurablePlugin: plugin_configuration,
        }
        with self.assertRaises(ConfigurationValueError):
            PluginsConfiguration(plugins_configuration_dict)

    def test_setitem_and_getitem_with_valid_configuration_should_set_and_return(self):
        plugin_configuration = {
            'check': 1337,
        }
        sut = PluginsConfiguration()
        sut[ConfigurablePlugin] = plugin_configuration
        self.assertEqual(plugin_configuration, sut[ConfigurablePlugin])

    def test_setitem_with_invalid_configuration_should_raise_configuration_error(self):
        plugin_configuration = 1337
        sut = PluginsConfiguration()
        with self.assertRaises(ConfigurationValueError):
            sut[ConfigurablePlugin] = plugin_configuration

    def test_contains(self):
        sut = PluginsConfiguration()
        sut[NonConfigurablePlugin] = None
        self.assertIn(NonConfigurablePlugin, sut)

    def test_iter(self):
        sut = PluginsConfiguration()
        sut[NonConfigurablePlugin] = None
        self.assertSequenceEqual([(NonConfigurablePlugin, None)], list(sut))

    def test_len(self):
        sut = PluginsConfiguration()
        sut[NonConfigurablePlugin] = None
        self.assertEqual(1, len(sut))


class LocaleConfigurationTest(TestCase):
    def test_locale(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        self.assertEquals(locale, sut.locale)

    def test_alias_implicit(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        self.assertEquals(locale, sut.alias)

    def test_alias_explicit(self):
        locale = 'nl-NL'
        alias = 'nl'
        sut = LocaleConfiguration(locale, alias)
        self.assertEquals(alias, sut.alias)

    @parameterized.expand([
        (False, LocaleConfiguration('nl', 'NL'), 'not a locale configuration'),
        (False, LocaleConfiguration('nl', 'NL'), 999),
        (False, LocaleConfiguration('nl', 'NL'), object()),
    ])
    def test_eq(self, expected, sut, other):
        self.assertEquals(expected, sut == other)


class ConfigurationTest(TestCase):
    def test_output_directory_path(self):
        output_directory_path = '/tmp/betty'
        sut = Configuration(output_directory_path, 'https://example.com')
        self.assertEquals(output_directory_path, sut.output_directory_path)

    def test_www_directory_path_with_absolute_path(self):
        output_directory_path = '/tmp/betty'
        sut = Configuration(output_directory_path, 'https://example.com')
        expected = join(output_directory_path, 'www')
        self.assertEquals(expected, sut.www_directory_path)

    def test_assets_directory_path_without_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        self.assertIsNone(sut.assets_directory_path)

    def test_assets_directory_path_with_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        assets_directory_path = '/tmp/betty-assets'
        sut.assets_directory_path = assets_directory_path
        self.assertEquals(assets_directory_path,
                          sut.assets_directory_path)

    def test_root_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        configured_root_path = '/betty'
        expected_root_path = '/betty/'
        sut.root_path = configured_root_path
        self.assertEquals(expected_root_path, sut.root_path)

    def test_clean_urls(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        clean_urls = True
        sut.clean_urls = clean_urls
        self.assertEquals(clean_urls, sut.clean_urls)

    def test_content_negotiation(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        content_negotiation = True
        sut.content_negotiation = content_negotiation
        self.assertEquals(content_negotiation, sut.content_negotiation)

    def test_clean_urls_implied_by_content_negotiation(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        sut.content_negotiation = True
        self.assertTrue(sut.clean_urls)

    def test_author_without_author(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        self.assertIsNone(sut.author)

    def test_author_with_author(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        author = 'Bart'
        sut.author = author
        self.assertEquals(author, sut.author)


class FromTest(TestCase):
    @contextmanager
    def _build_minimal_config(self) -> Dict:
        output_directory = TemporaryDirectory()
        try:
            yield {
                'output': output_directory.name,
                'base_url': 'https://example.com',
            }
        finally:
            output_directory.cleanup()

    def _writes(self, config: str, extension: str):
        f = NamedTemporaryFile(mode='r+', suffix='.' + extension)
        f.write(config)
        f.seek(0)
        return f

    def _write(self, config_dict: Dict[str, Any]):
        return self._writes(json.dumps(config_dict), 'json')

    @parameterized.expand([
        ('json', json.dumps),
        ('yaml', yaml.safe_dump),
        ('yml', yaml.safe_dump),
    ])
    def test_from_file_should_parse_minimal(self, extension, dumper):
        with self._build_minimal_config() as config_dict:
            with self._writes(dumper(config_dict), extension) as f:
                configuration = from_file(f)
            self.assertEquals(config_dict['output'], configuration.output_directory_path)
            self.assertEquals(config_dict['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertEquals('production', configuration.mode)
            self.assertEquals('/', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_from_file_should_parse_title(self):
        title = 'My first Betty site'
        with self._build_minimal_config() as config_dict:
            config_dict['title'] = title
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(title, configuration.title)

    def test_from_file_should_parse_author(self):
        author = 'Bart'
        with self._build_minimal_config() as config_dict:
            config_dict['author'] = author
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(author, configuration.author)

    def test_from_file_should_parse_locale_locale(self):
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        with self._build_minimal_config() as config_dict:
            config_dict['locales'] = [locale_config]
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale),
            }), configuration.locales)

    def test_from_file_should_parse_locale_alias(self):
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        with self._build_minimal_config() as config_dict:
            config_dict['locales'] = [locale_config]
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale, alias),
            }), configuration.locales)

    def test_from_file_should_root_path(self):
        configured_root_path = '/betty'
        expected_root_path = '/betty/'
        with self._build_minimal_config() as config_dict:
            config_dict['root_path'] = configured_root_path
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(expected_root_path, configuration.root_path)

    def test_from_file_should_clean_urls(self):
        clean_urls = True
        with self._build_minimal_config() as config_dict:
            config_dict['clean_urls'] = clean_urls
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(clean_urls, configuration.clean_urls)

    def test_from_file_should_content_negotiation(self):
        content_negotiation = True
        with self._build_minimal_config() as config_dict:
            config_dict['content_negotiation'] = content_negotiation
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        ('production',),
        ('development',),
    ])
    def test_from_file_should_parse_mode(self, mode: str):
        with self._build_minimal_config() as config_dict:
            config_dict['mode'] = mode
            with self._write(config_dict) as f:
                configuration = from_file(f)
            self.assertEquals(mode, configuration.mode)

    def test_from_file_should_parse_assets_directory_path(self):
        with TemporaryDirectory() as assets_directory_path:
            with self._build_minimal_config() as config_dict:
                config_dict['assets_directory_path'] = assets_directory_path
                with self._write(config_dict) as f:
                    configuration = from_file(f)
                self.assertEquals(assets_directory_path, configuration.assets_directory_path)

    def test_from_file_should_parse_one_plugin_with_configuration(self):
        with self._build_minimal_config() as config_dict:
            plugin_configuration = {
                'check': 1337,
            }
            config_dict['plugins'] = {
                ConfigurablePlugin.name(): plugin_configuration,
            }
            with self._write(config_dict) as f:
                configuration = from_file(f)
            expected = {
                ConfigurablePlugin: plugin_configuration,
            }
            self.assertEquals(expected, dict(configuration.plugins))

    def test_from_file_should_parse_one_plugin_without_configuration(self):
        with self._build_minimal_config() as config_dict:
            config_dict['plugins'] = {
                NonConfigurablePlugin.name(): None,
            }
            with self._write(config_dict) as f:
                configuration = from_file(f)
            expected = {
                NonConfigurablePlugin: None,
            }
            self.assertEquals(expected, dict(configuration.plugins))

    def test_from_file_should_error_unknown_format(self):
        with self._writes('', 'abc') as f:
            with self.assertRaises(ConfigurationValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_json(self):
        with self._writes('', 'json') as f:
            with self.assertRaises(ConfigurationValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_yaml(self):
        with self._writes('"foo', 'yaml') as f:
            with self.assertRaises(ConfigurationValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_config(self):
        config_dict = {}
        with self._write(config_dict) as f:
            with self.assertRaises(ConfigurationValueError):
                from_file(f)
