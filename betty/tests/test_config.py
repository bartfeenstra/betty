import json
from collections import OrderedDict
from contextlib import contextmanager
from os.path import join
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict

import yaml
from parameterized import parameterized
from voluptuous import Schema, Required

from betty.config import ConfigurationValueError, LocaleConfiguration, Configuration, from_file, _from_dict, from_json, \
    from_yaml
from betty.extension import Extension, NO_CONFIGURATION
from betty.app import App
from betty.tests import TestCase


@contextmanager
def _build_minimal_config() -> Dict:
    output_directory = TemporaryDirectory()
    try:
        yield {
            'output': output_directory.name,
            'base_url': 'https://example.com',
        }
    finally:
        output_directory.cleanup()


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


class NonConfigurableExtension(Extension):
    pass  # pragma: no cover


class ConfigurableExtension(Extension):
    configuration_schema: Schema = Schema({
        Required('check'): lambda x: x,
        Required('default', default='I will always be there for you.'): lambda x: x,
    })

    def __init__(self, check, default):
        self.check = check
        self.default = default

    @classmethod
    def new_for_app(cls, app: App, configuration: Any = NO_CONFIGURATION):
        return cls(configuration['check'], configuration['default'])


class FromDictTest(TestCase):
    @parameterized.expand([
        ('json', json.dumps),
        ('yaml', yaml.safe_dump),
        ('yml', yaml.safe_dump),
    ])
    def test_should_parse_minimal(self, extension, dumper) -> None:
        with _build_minimal_config() as configuration_dict:
            configuration = _from_dict(configuration_dict)
            self.assertEquals(configuration_dict['output'], configuration.output_directory_path)
            self.assertEquals(configuration_dict['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertEquals('production', configuration.mode)
            self.assertEquals('/', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_should_parse_title(self) -> None:
        title = 'My first Betty site'
        with _build_minimal_config() as configuration_dict:
            configuration_dict['title'] = title
            configuration = _from_dict(configuration_dict)
            self.assertEquals(title, configuration.title)

    def test_should_parse_author(self) -> None:
        author = 'Bart'
        with _build_minimal_config() as configuration_dict:
            configuration_dict['author'] = author
            configuration = _from_dict(configuration_dict)
            self.assertEquals(author, configuration.author)

    def test_should_parse_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        with _build_minimal_config() as configuration_dict:
            configuration_dict['locales'] = [locale_config]
            configuration = _from_dict(configuration_dict)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale),
            }), configuration.locales)

    def test_should_parse_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        with _build_minimal_config() as configuration_dict:
            configuration_dict['locales'] = [locale_config]
            configuration = _from_dict(configuration_dict)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale, alias),
            }), configuration.locales)

    def test_should_root_path(self) -> None:
        configured_root_path = '/betty'
        expected_root_path = '/betty/'
        with _build_minimal_config() as configuration_dict:
            configuration_dict['root_path'] = configured_root_path
            configuration = _from_dict(configuration_dict)
            self.assertEquals(expected_root_path, configuration.root_path)

    def test_should_clean_urls(self) -> None:
        clean_urls = True
        with _build_minimal_config() as configuration_dict:
            configuration_dict['clean_urls'] = clean_urls
            configuration = _from_dict(configuration_dict)
            self.assertEquals(clean_urls, configuration.clean_urls)

    def test_should_content_negotiation(self) -> None:
        content_negotiation = True
        with _build_minimal_config() as configuration_dict:
            configuration_dict['content_negotiation'] = content_negotiation
            configuration = _from_dict(configuration_dict)
            self.assertEquals(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        ('production',),
        ('development',),
    ])
    def test_should_parse_mode(self, mode: str) -> None:
        with _build_minimal_config() as configuration_dict:
            configuration_dict['mode'] = mode
            configuration = _from_dict(configuration_dict)
            self.assertEquals(mode, configuration.mode)

    def test_should_parse_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            with _build_minimal_config() as configuration_dict:
                configuration_dict['assets_directory_path'] = assets_directory_path
                configuration = _from_dict(configuration_dict)
                self.assertEquals(assets_directory_path, configuration.assets_directory_path)

    def test_should_parse_one_extension_with_configuration(self) -> None:
        with _build_minimal_config() as configuration_dict:
            extension_configuration = {
                'check': 1337,
            }
            configuration_dict['extensions'] = {
                ConfigurableExtension.name(): extension_configuration,
            }
            configuration = _from_dict(configuration_dict)
            expected = {
                ConfigurableExtension: {
                    'check': 1337,
                    'default': 'I will always be there for you.',
                },
            }
            self.assertEquals(expected, dict(configuration.extensions))

    def test_should_parse_one_extension_without_configuration(self) -> None:
        with _build_minimal_config() as configuration_dict:
            configuration_dict['extensions'] = {
                NonConfigurableExtension.name(): None,
            }
            configuration = _from_dict(configuration_dict)
            expected = {
                NonConfigurableExtension: None,
            }
            self.assertEquals(expected, dict(configuration.extensions))

    def test_extension_with_invalid_configuration_should_raise_error(self):
        with _build_minimal_config() as configuration_dict:
            configuration_dict['extensions'] = {
                ConfigurableExtension.name(): 1337,
            }
            with self.assertRaises(ConfigurationValueError):
                _from_dict(configuration_dict)

    def test_unknown_extension_type_name_should_error(self):
        with _build_minimal_config() as configuration_dict:
            configuration_dict['extensions'] = {
                'non.existent.type': None,
            }
            with self.assertRaises(ConfigurationValueError):
                _from_dict(configuration_dict)

    def test_not_an_extension_type_name_should_error(self):
        with _build_minimal_config() as configuration_dict:
            configuration_dict['extensions'] = {
                '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
            }
            with self.assertRaises(ConfigurationValueError):
                _from_dict(configuration_dict)

    def test_should_error_if_invalid_config(self) -> None:
        configuration_dict = {}
        with self.assertRaises(ConfigurationValueError):
            _from_dict(configuration_dict)


class FromJsonTest(TestCase):
    def test_should_error_if_invalid_json(self) -> None:
        with self.assertRaises(ConfigurationValueError):
            from_json('')


class FromYamlTest(TestCase):
    def test_should_error_if_invalid_yaml(self) -> None:
        with self.assertRaises(ConfigurationValueError):
            from_yaml('"foo')


class FromFileTest(TestCase):
    def _writes(self, config: str, extension: str) -> object:
        f = NamedTemporaryFile(mode='r+', suffix='.' + extension)
        f.write(config)
        f.seek(0)
        return f

    def _write(self, configuration_dict: Dict[str, Any]) -> object:
        return self._writes(json.dumps(configuration_dict), 'json')

    def test_should_error_unknown_format(self) -> None:
        with self._writes('', 'abc') as f:
            with self.assertRaises(ConfigurationValueError):
                from_file(f)
