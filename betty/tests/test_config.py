import json
from collections import OrderedDict
from contextlib import contextmanager
from os.path import join
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict

from parameterized import parameterized
from voluptuous import Schema, Required, Invalid, All

from betty import extension
from betty.config import LocaleConfiguration, Configuration, _from_dict, from_yaml, from_file, from_json, _to_dict, \
    ConfigurationError, ExtensionConfiguration
from betty.extension import Configuration as ExtensionTypeConfiguration, Extension
from betty.tests import TestCase
from betty.tests.test_react import ReactiveTestCase


@contextmanager
def _build_minimal_configuration_dict() -> Dict:
    output_directory = TemporaryDirectory()
    try:
        yield {
            'output': output_directory.name,
            'base_url': 'https://example.com',
        }
    finally:
        output_directory.cleanup()


@contextmanager
def _build_minimal_configuration() -> Configuration:
    output_directory = TemporaryDirectory()
    try:
        yield Configuration(output_directory.name, 'https://example.com')
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


class ExtensionConfigurationTest(ReactiveTestCase):
    def test_extension_type(self):
        extension_type = Extension
        sut = ExtensionConfiguration(extension_type)
        self.assertEquals(extension_type, sut.extension_type)

    def test_enabled(self):
        enabled = True
        sut = ExtensionConfiguration(Extension, enabled)
        self.assertEquals(enabled, sut.enabled)
        with self.assert_reactor_called(sut):
            sut.enabled = False

    def test_configuration(self):
        extension_type_configuration = ExtensionTypeConfiguration()
        sut = ExtensionConfiguration(Extension, True, extension_type_configuration)
        self.assertEquals(extension_type_configuration, sut.extension_type_configuration)
        with self.assert_reactor_called(sut):
            extension_type_configuration.react.trigger()


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

    def test_base_url(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        base_url = 'https://example.com'
        sut.base_url = base_url
        self.assertEquals(base_url, sut.base_url)

    def test_base_url_without_scheme_should_error(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        with self.assertRaises(ConfigurationError):
            sut.base_url = '/'

    def test_base_url_without_path_should_error(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        with self.assertRaises(ConfigurationError):
            sut.base_url = 'file://'

    def test_root_path(self):
        sut = Configuration('/tmp/betty', 'https://example.com')
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
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


class NonConfigurableExtension(extension.Extension):
    pass  # pragma: no cover


class ConfigurableExtensionConfiguration(extension.Configuration):
    def __init__(self, check, default):
        super().__init__()
        self.check = check
        self.default = default

    def __eq__(self, other):
        return self.check == other.check and self.default == other.default


class ConfigurableExtension(extension.ConfigurableExtension):
    _CONFIGURATION_SCHEMA: Schema = Schema(All({
        Required('check'): lambda x: x,
        Required('default', default='I will always be there for you.'): lambda x: x,
    }, lambda configuration_dict: ConfigurableExtensionConfiguration(**configuration_dict)))

    @classmethod
    def default_configuration(cls) -> ConfigurableExtensionConfiguration:
        return ConfigurableExtensionConfiguration(None, None)

    @classmethod
    def configuration_from_dict(cls, configuration_dict: Dict) -> ConfigurableExtensionConfiguration:
        try:
            return cls._CONFIGURATION_SCHEMA(configuration_dict)
        except Invalid as e:
            raise ConfigurationError(e)

    @classmethod
    def configuration_to_dict(cls, configuration: ConfigurableExtensionConfiguration) -> Dict:
        return {
            'check': configuration.check,
            'default': configuration.default,
        }


class FromDictTest(TestCase):
    def test_should_load_minimal(self) -> None:
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration = _from_dict(configuration_dict)
            self.assertEquals(configuration_dict['output'], configuration.output_directory_path)
            self.assertEquals(configuration_dict['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertEquals('production', configuration.mode)
            self.assertEquals('', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_should_load_title(self) -> None:
        title = 'My first Betty site'
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['title'] = title
            configuration = _from_dict(configuration_dict)
            self.assertEquals(title, configuration.title)

    def test_should_load_author(self) -> None:
        author = 'Bart'
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['author'] = author
            configuration = _from_dict(configuration_dict)
            self.assertEquals(author, configuration.author)

    def test_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['locales'] = [locale_config]
            configuration = _from_dict(configuration_dict)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale),
            }), configuration.locales)

    def test_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['locales'] = [locale_config]
            configuration = _from_dict(configuration_dict)
            self.assertDictEqual(OrderedDict({
                locale: LocaleConfiguration(locale, alias),
            }), configuration.locales)

    def test_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['root_path'] = configured_root_path
            configuration = _from_dict(configuration_dict)
            self.assertEquals(expected_root_path, configuration.root_path)

    def test_should_clean_urls(self) -> None:
        clean_urls = True
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['clean_urls'] = clean_urls
            configuration = _from_dict(configuration_dict)
            self.assertEquals(clean_urls, configuration.clean_urls)

    def test_should_content_negotiation(self) -> None:
        content_negotiation = True
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['content_negotiation'] = content_negotiation
            configuration = _from_dict(configuration_dict)
            self.assertEquals(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        ('production',),
        ('development',),
    ])
    def test_should_load_mode(self, mode: str) -> None:
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['mode'] = mode
            configuration = _from_dict(configuration_dict)
            self.assertEquals(mode, configuration.mode)

    def test_should_load_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            with _build_minimal_configuration_dict() as configuration_dict:
                configuration_dict['assets'] = assets_directory_path
                configuration = _from_dict(configuration_dict)
                self.assertEquals(assets_directory_path, configuration.assets_directory_path)

    def test_should_load_one_extension_with_configuration(self) -> None:
        with _build_minimal_configuration_dict() as configuration_dict:
            extension_configuration = {
                'check': 1337,
            }
            configuration_dict['extensions'] = {
                ConfigurableExtension.name(): {
                    'configuration': extension_configuration,
                },
            }
            configuration = _from_dict(configuration_dict)
            expected = {
                ConfigurableExtension: ExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
                    check=1337,
                    default='I will always be there for you.',
                )),
            }
            self.assertEquals(expected, configuration.extensions)

    def test_should_load_one_extension_without_configuration(self) -> None:
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['extensions'] = {
                NonConfigurableExtension.name(): {},
            }
            configuration = _from_dict(configuration_dict)
            expected = {
                NonConfigurableExtension: ExtensionConfiguration(NonConfigurableExtension, True),
            }
            self.assertEquals(expected, configuration.extensions)

    def test_extension_with_invalid_configuration_should_raise_error(self):
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['extensions'] = {
                ConfigurableExtension.name(): 1337,
            }
            with self.assertRaises(ConfigurationError):
                _from_dict(configuration_dict)

    def test_unknown_extension_type_name_should_error(self):
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['extensions'] = {
                'non.existent.type': None,
            }
            with self.assertRaises(ConfigurationError):
                _from_dict(configuration_dict)

    def test_not_an_extension_type_name_should_error(self):
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['extensions'] = {
                '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
            }
            with self.assertRaises(ConfigurationError):
                _from_dict(configuration_dict)

    def test_should_load_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        with _build_minimal_configuration_dict() as configuration_dict:
            configuration_dict['theme'] = {
                'background_image_id': background_image_id
            }
            configuration = _from_dict(configuration_dict)
            self.assertEquals(background_image_id, configuration.theme.background_image_id)

    def test_should_error_if_invalid_config(self) -> None:
        configuration_dict = {}
        with self.assertRaises(ConfigurationError):
            _from_dict(configuration_dict)


class FromJsonTest(TestCase):
    def test_should_error_if_invalid_json(self) -> None:
        with self.assertRaises(ConfigurationError):
            from_json('')


class FromYamlTest(TestCase):
    def test_should_error_if_invalid_yaml(self) -> None:
        with self.assertRaises(ConfigurationError):
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
            with self.assertRaises(ConfigurationError):
                from_file(f)


class ToDictTest(TestCase):
    def test_should_dump_minimal(self) -> None:
        with _build_minimal_configuration() as configuration:
            configuration_dict = _to_dict(configuration)
            self.assertEquals(configuration_dict['output'], configuration.output_directory_path)
            self.assertEquals(configuration_dict['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertEquals('production', configuration.mode)
            self.assertEquals('', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_should_dump_title(self) -> None:
        title = 'My first Betty site'
        with _build_minimal_configuration() as configuration:
            configuration.title = title
            configuration_dict = _to_dict(configuration)
            self.assertEquals(title, configuration_dict['title'])

    def test_should_dump_author(self) -> None:
        author = 'Bart'
        with _build_minimal_configuration() as configuration:
            configuration.author = author
            configuration_dict = _to_dict(configuration)
            self.assertEquals(author, configuration_dict['author'])

    def test_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        with _build_minimal_configuration() as configuration:
            configuration.locales.clear()
            configuration.locales[locale] = locale_configuration
            configuration_dict = _to_dict(configuration)
            self.assertListEqual([
                {
                    'locale': locale,
                },
            ], configuration_dict['locales'])

    def test_should_dump_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_configuration = LocaleConfiguration(locale, alias)
        with _build_minimal_configuration() as configuration:
            configuration.locales.clear()
            configuration.locales[locale] = locale_configuration
            configuration_dict = _to_dict(configuration)
            self.assertListEqual([
                {
                    'locale': locale,
                    'alias': alias,
                },
            ], configuration_dict['locales'])

    def test_should_dump_root_path(self) -> None:
        root_path = 'betty'
        with _build_minimal_configuration() as configuration:
            configuration.root_path = root_path
            configuration_dict = _to_dict(configuration)
            self.assertEquals(root_path, configuration_dict['root_path'])

    def test_should_dump_clean_urls(self) -> None:
        clean_urls = True
        with _build_minimal_configuration() as configuration:
            configuration.clean_urls = clean_urls
            configuration_dict = _to_dict(configuration)
            self.assertEquals(clean_urls, configuration_dict['clean_urls'])

    def test_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        with _build_minimal_configuration() as configuration:
            configuration.content_negotiation = content_negotiation
            configuration_dict = _to_dict(configuration)
            self.assertEquals(content_negotiation, configuration_dict['content_negotiation'])

    @parameterized.expand([
        ('production',),
        ('development',),
    ])
    def test_should_dump_mode(self, mode: str) -> None:
        with _build_minimal_configuration() as configuration:
            configuration.mode = mode
            configuration_dict = _to_dict(configuration)
            self.assertEquals(mode, configuration_dict['mode'])

    def test_should_dump_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            with _build_minimal_configuration() as configuration:
                configuration.assets_directory_path = assets_directory_path
                configuration_dict = _to_dict(configuration)
                self.assertEquals(assets_directory_path, configuration_dict['assets'])

    def test_should_dump_one_extension_with_configuration(self) -> None:
        with _build_minimal_configuration() as configuration:
            configuration.extensions[ConfigurableExtension] = ExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
                check=1337,
                default='I will always be there for you.',
            ))
            configuration_dict = _to_dict(configuration)
            expected = {
                ConfigurableExtension.name(): {
                    'enabled': True,
                    'configuration': {
                        'check': 1337,
                        'default': 'I will always be there for you.',
                    },
                },
            }
            self.assertEquals(expected, configuration_dict['extensions'])

    def test_should_dump_one_extension_without_configuration(self) -> None:
        with _build_minimal_configuration() as configuration:
            configuration.extensions[NonConfigurableExtension] = ExtensionConfiguration(NonConfigurableExtension)
            configuration_dict = _to_dict(configuration)
            expected = {
                NonConfigurableExtension.name(): {
                    'enabled': True,
                    'configuration': {},
                },
            }
            self.assertEquals(expected, configuration_dict['extensions'])

    def test_should_error_if_invalid_config(self) -> None:
        configuration_dict = {}
        with self.assertRaises(ConfigurationError):
            _from_dict(configuration_dict)

    def test_should_dump_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        with _build_minimal_configuration() as configuration:
            configuration.theme.background_image_id = background_image_id
            configuration_dict = _to_dict(configuration)
            self.assertEquals(background_image_id, configuration_dict['theme']['background_image_id'])
