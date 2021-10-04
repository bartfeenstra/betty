from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Any, Type, List, Set

from parameterized import parameterized
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty import app
from betty.app import Configuration, LocaleConfiguration, LocalesConfiguration, AppExtensionConfiguration, Extension, \
    AppExtensionsConfiguration, ConfigurationError, ConfigurableExtension, App, CyclicDependencyError
from betty.asyncio import sync
from betty.config import Configuration as GenericConfiguration
from betty.model.ancestry import Ancestry
from betty.tests import TestCase


@contextmanager
def _build_minimal_app_dumped_configuration() -> Dict:
    output_directory = TemporaryDirectory()
    try:
        yield {
            'output': output_directory.name,
            'base_url': 'https://example.com',
        }
    finally:
        output_directory.cleanup()


@contextmanager
def _build_minimal_app_configuration() -> Configuration:
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


class LocalesConfigurationTest(TestCase):
    def test_getitem(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertEquals(locale_configuration_a, sut['nl-NL'])

    def test_delitem(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['nl-NL']
        self.assertCountEqual([locale_configuration_b], sut)

    def test_delitem_with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        with self.assertRaises(ConfigurationError):
            del sut['nl-NL']

    def test_iter(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertCountEqual([locale_configuration_a, locale_configuration_b], iter(sut))

    def test_len(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_eq(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        other = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEquals(other, sut)

    def test_contains(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertIn('nl-NL', sut)
            self.assertNotIn('en-US', sut)

    def test_repr(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertIsInstance(repr(sut), str)

    def test_add(self) -> None:
        sut = LocalesConfiguration()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.add(LocaleConfiguration('nl-NL'))

    def test_default_without_explicit_locale_configurations(self):
        sut = LocalesConfiguration()
        self.assertEquals(LocaleConfiguration('en-US'), sut.default)

    def test_default_without_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        self.assertEquals(locale_configuration_a, sut.default)

    def test_default_with_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        sut.default = locale_configuration_b
        self.assertEquals(locale_configuration_b, sut.default)


class AppExtensionConfigurationTest(TestCase):
    def test_extension_type(self):
        extension_type = Extension
        sut = AppExtensionConfiguration(extension_type)
        self.assertEquals(extension_type, sut.extension_type)

    def test_enabled(self):
        enabled = True
        sut = AppExtensionConfiguration(Extension, enabled)
        self.assertEquals(enabled, sut.enabled)
        with assert_reactor_called(sut):
            sut.enabled = False

    def test_configuration(self):
        extension_type_configuration = GenericConfiguration()
        sut = AppExtensionConfiguration(Extension, True, extension_type_configuration)
        self.assertEquals(extension_type_configuration, sut.extension_configuration)
        with assert_reactor_called(sut):
            extension_type_configuration.react.trigger()


class AppExtensionsConfigurationTest(TestCase):
    def test_getitem(self) -> None:
        app_extension_configuration_a = AppExtensionConfiguration(DummyConfigurableExtension)
        sut = AppExtensionsConfiguration([
            app_extension_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertEquals(app_extension_configuration_a, sut[DummyConfigurableExtension])

    def test_delitem(self) -> None:
        app_extension_configuration = AppExtensionConfiguration(DummyConfigurableExtension)
        sut = AppExtensionsConfiguration([
            app_extension_configuration,
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[DummyConfigurableExtension]
        self.assertCountEqual([], sut)
        self.assertCountEqual([], app_extension_configuration.react._reactors)

    def test_iter(self) -> None:
        app_extension_configuration_a = AppExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = AppExtensionConfiguration(DummyNonConfigurableExtension)
        sut = AppExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertCountEqual([app_extension_configuration_a, app_extension_configuration_b], iter(sut))

    def test_len(self) -> None:
        app_extension_configuration_a = AppExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = AppExtensionConfiguration(DummyNonConfigurableExtension)
        sut = AppExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_eq(self) -> None:
        app_extension_configuration_a = AppExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = AppExtensionConfiguration(DummyNonConfigurableExtension)
        sut = AppExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        other = AppExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEquals(other, sut)

    def test_add(self) -> None:
        sut = AppExtensionsConfiguration()
        app_extension_configuration = AppExtensionConfiguration(DummyConfigurableExtension)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.add(app_extension_configuration)
        self.assertEquals(app_extension_configuration, sut[DummyConfigurableExtension])
        with assert_reactor_called(sut):
            app_extension_configuration.react.trigger()


class ConfigurationTest(TestCase):
    def test_output_directory_path(self):
        output_directory_path = Path('~')
        sut = Configuration(output_directory_path, 'https://example.com')
        self.assertEquals(output_directory_path, sut.output_directory_path)

    def test_www_directory_path_with_absolute_path(self):
        output_directory_path = Path('~')
        sut = Configuration(output_directory_path, 'https://example.com')
        expected = output_directory_path / 'www'
        self.assertEquals(expected, sut.www_directory_path)

    def test_assets_directory_path_without_path(self):
        sut = Configuration('~', 'https://example.com')
        self.assertIsNone(sut.assets_directory_path)

    def test_assets_directory_path_with_path(self):
        sut = Configuration('~', 'https://example.com')
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
        sut = Configuration('~', 'https://example.com')
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        sut.root_path = configured_root_path
        self.assertEquals(expected_root_path, sut.root_path)

    def test_clean_urls(self):
        sut = Configuration('~', 'https://example.com')
        clean_urls = True
        sut.clean_urls = clean_urls
        self.assertEquals(clean_urls, sut.clean_urls)

    def test_content_negotiation(self):
        sut = Configuration('~', 'https://example.com')
        content_negotiation = True
        sut.content_negotiation = content_negotiation
        self.assertEquals(content_negotiation, sut.content_negotiation)

    def test_clean_urls_implied_by_content_negotiation(self):
        sut = Configuration('~', 'https://example.com')
        sut.content_negotiation = True
        self.assertTrue(sut.clean_urls)

    def test_author_without_author(self):
        sut = Configuration('~', 'https://example.com')
        self.assertIsNone(sut.author)

    def test_author_with_author(self):
        sut = Configuration('~', 'https://example.com')
        author = 'Bart'
        sut.author = author
        self.assertEquals(author, sut.author)

    def test_load_should_load_minimal(self) -> None:
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(Path(dumped_configuration['output']).expanduser().resolve(), configuration.output_directory_path)
            self.assertEquals(dumped_configuration['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertFalse(configuration.debug)
            self.assertEquals('', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_load_should_load_title(self) -> None:
        title = 'My first Betty site'
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['title'] = title
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(title, configuration.title)

    def test_load_should_load_author(self) -> None:
        author = 'Bart'
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['author'] = author
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(author, configuration.author)

    def test_load_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['locales'] = [locale_config]
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(LocalesConfiguration([LocaleConfiguration(locale)]), configuration.locales)

    def test_load_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['locales'] = [locale_config]
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(LocalesConfiguration([LocaleConfiguration(locale, alias)]), configuration.locales)

    def test_load_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['root_path'] = configured_root_path
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(expected_root_path, configuration.root_path)

    def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['clean_urls'] = clean_urls
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(clean_urls, configuration.clean_urls)

    def test_load_should_content_negotiation(self) -> None:
        content_negotiation = True
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['content_negotiation'] = content_negotiation
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_load_should_load_debug(self, debug: bool) -> None:
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['debug'] = debug
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(debug, configuration.debug)

    def test_load_should_load_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            with _build_minimal_app_dumped_configuration() as dumped_configuration:
                dumped_configuration['assets'] = assets_directory_path
                configuration = Configuration.load(dumped_configuration)
                self.assertEquals(Path(assets_directory_path).expanduser().resolve(), configuration.assets_directory_path)

    def test_load_should_load_one_extension_with_configuration(self) -> None:
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            extension_configuration = {
                'check': 1337,
            }
            dumped_configuration['extensions'] = {
                DummyConfigurableExtension.name(): {
                    'configuration': extension_configuration,
                },
            }
            configuration = Configuration.load(dumped_configuration)
            expected = AppExtensionsConfiguration([
                AppExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
                    check=1337,
                    default='I will always be there for you.',
                )),
            ])
            self.assertEquals(expected, configuration.extensions)

    def test_load_should_load_one_extension_without_configuration(self) -> None:
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['extensions'] = {
                DummyNonConfigurableExtension.name(): {},
            }
            configuration = Configuration.load(dumped_configuration)
            expected = AppExtensionsConfiguration([
                AppExtensionConfiguration(DummyNonConfigurableExtension, True),
            ])
            self.assertEquals(expected, configuration.extensions)

    def test_load_extension_with_invalid_configuration_should_raise_error(self):
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['extensions'] = {
                DummyConfigurableExtension.name(): 1337,
            }
            with self.assertRaises(ConfigurationError):
                Configuration.load(dumped_configuration)

    def test_load_unknown_extension_type_name_should_error(self):
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['extensions'] = {
                'non.existent.type': None,
            }
            with self.assertRaises(ConfigurationError):
                Configuration.load(dumped_configuration)

    def test_load_not_an_extension_type_name_should_error(self):
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['extensions'] = {
                '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
            }
            with self.assertRaises(ConfigurationError):
                Configuration.load(dumped_configuration)

    def test_load_should_load_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        with _build_minimal_app_dumped_configuration() as dumped_configuration:
            dumped_configuration['theme'] = {
                'background_image_id': background_image_id
            }
            configuration = Configuration.load(dumped_configuration)
            self.assertEquals(background_image_id, configuration.theme.background_image_id)

    def test_load_should_error_if_invalid_config(self) -> None:
        dumped_configuration = {}
        with self.assertRaises(ConfigurationError):
            Configuration.load(dumped_configuration)

    def test_dump_should_dump_minimal(self) -> None:
        with _build_minimal_app_configuration() as configuration:
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(dumped_configuration['output'], str(configuration.output_directory_path))
            self.assertEquals(dumped_configuration['base_url'], configuration.base_url)
            self.assertEquals('Betty', configuration.title)
            self.assertIsNone(configuration.author)
            self.assertEquals(False, configuration.debug)
            self.assertEquals('', configuration.root_path)
            self.assertFalse(configuration.clean_urls)
            self.assertFalse(configuration.content_negotiation)

    def test_dump_should_dump_title(self) -> None:
        title = 'My first Betty site'
        with _build_minimal_app_configuration() as configuration:
            configuration.title = title
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(title, dumped_configuration['title'])

    def test_dump_should_dump_author(self) -> None:
        author = 'Bart'
        with _build_minimal_app_configuration() as configuration:
            configuration.author = author
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(author, dumped_configuration['author'])

    def test_dump_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        with _build_minimal_app_configuration() as configuration:
            configuration.locales.replace([locale_configuration])
            dumped_configuration = Configuration.dump(configuration)
            self.assertListEqual([
                {
                    'locale': locale,
                },
            ], dumped_configuration['locales'])

    def test_dump_should_dump_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_configuration = LocaleConfiguration(locale, alias)
        with _build_minimal_app_configuration() as configuration:
            configuration.locales.replace([locale_configuration])
            dumped_configuration = Configuration.dump(configuration)
            self.assertListEqual([
                {
                    'locale': locale,
                    'alias': alias,
                },
            ], dumped_configuration['locales'])

    def test_dump_should_dump_root_path(self) -> None:
        root_path = 'betty'
        with _build_minimal_app_configuration() as configuration:
            configuration.root_path = root_path
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(root_path, dumped_configuration['root_path'])

    def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        with _build_minimal_app_configuration() as configuration:
            configuration.clean_urls = clean_urls
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(clean_urls, dumped_configuration['clean_urls'])

    def test_dump_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        with _build_minimal_app_configuration() as configuration:
            configuration.content_negotiation = content_negotiation
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(content_negotiation, dumped_configuration['content_negotiation'])

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_dump_should_dump_debug(self, debug: bool) -> None:
        with _build_minimal_app_configuration() as configuration:
            configuration.debug = debug
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(debug, dumped_configuration['debug'])

    def test_dump_should_dump_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            with _build_minimal_app_configuration() as configuration:
                configuration.assets_directory_path = assets_directory_path
                dumped_configuration = Configuration.dump(configuration)
                self.assertEquals(assets_directory_path, dumped_configuration['assets'])

    def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        with _build_minimal_app_configuration() as configuration:
            configuration.extensions.add(AppExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
                check=1337,
                default='I will always be there for you.',
            )))
            dumped_configuration = Configuration.dump(configuration)
            expected = {
                DummyConfigurableExtension.name(): {
                    'enabled': True,
                    'configuration': {
                        'check': 1337,
                        'default': 'I will always be there for you.',
                    },
                },
            }
            self.assertEquals(expected, dumped_configuration['extensions'])

    def test_dump_should_dump_one_extension_without_configuration(self) -> None:
        with _build_minimal_app_configuration() as configuration:
            configuration.extensions.add(AppExtensionConfiguration(DummyNonConfigurableExtension))
            dumped_configuration = Configuration.dump(configuration)
            expected = {
                DummyNonConfigurableExtension.name(): {
                    'enabled': True,
                },
            }
            self.assertEquals(expected, dumped_configuration['extensions'])

    def test_dump_should_error_if_invalid_config(self) -> None:
        dumped_configuration = {}
        with self.assertRaises(ConfigurationError):
            Configuration.load(dumped_configuration)

    def test_dump_should_dump_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        with _build_minimal_app_configuration() as configuration:
            configuration.theme.background_image_id = background_image_id
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(background_image_id, dumped_configuration['theme']['background_image_id'])


class DummyNonConfigurableExtension(Extension):
    pass  # pragma: no cover


class DummyConfigurableExtensionConfiguration(GenericConfiguration):
    def __init__(self, check, default):
        super().__init__()
        self.check = check
        self.default = default

    def __eq__(self, other):
        return self.check == other.check and self.default == other.default

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError

        if 'check' not in dumped_configuration:
            raise ConfigurationError

        default = dumped_configuration['default'] if 'default' in dumped_configuration else 'I will always be there for you.'

        return cls(dumped_configuration['check'], default)

    def dump(self) -> Any:
        return {
            'check': self.check,
            'default': self.default,
        }


class DummyConfigurableExtension(ConfigurableExtension):
    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return DummyConfigurableExtensionConfiguration

    @classmethod
    def default_configuration(cls) -> DummyConfigurableExtensionConfiguration:
        return DummyConfigurableExtensionConfiguration(None, None)


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackableExtension(Extension, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass  # pragma: no cover


class ConfigurableExtensionConfiguration(GenericConfiguration):
    def __init__(self, check):
        super().__init__()
        self.check = check

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError
        if 'check' not in dumped_configuration:
            raise ConfigurationError
        return cls(dumped_configuration['check'])

    def dump(self) -> Any:
        return {
            'check': self.check
        }


class ConfigurableExtension(app.ConfigurableExtension):
    @classmethod
    def default_configuration(cls) -> Configuration:
        return ConfigurableExtensionConfiguration(None)

    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return ConfigurableExtensionConfiguration


class CyclicDependencyOneExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyTwoExtension}


class CyclicDependencyTwoExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyOneExtension}


class DependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class AlsoDependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class DependsOnNonConfigurableExtensionExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {DependsOnNonConfigurableExtensionExtension}


class ComesBeforeNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_before(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class ComesAfterNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class AppTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'output_directory_path': '/tmp/path/to/site',
        'base_url': 'https://example.com',
    }

    @sync
    async def test_ancestry(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertIsInstance(sut.ancestry, Ancestry)

    @sync
    async def test_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(configuration, sut.configuration)

    @sync
    async def test_extensions_with_one_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_with_one_configurable_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.extensions.add(AppExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
            check=check,
        )))
        async with App(configuration) as sut:
            self.assertIsInstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
            self.assertEquals(check, sut.extensions[ConfigurableExtension]._configuration.check)

    @sync
    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(DependsOnNonConfigurableExtensionExtension,
                              type(carrier[1]))
            self.assertEquals(
                DependsOnNonConfigurableExtensionExtensionExtension, type(carrier[2]))

    @sync
    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
        configuration.extensions.add(AppExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertIn(DependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])
            self.assertIn(AlsoDependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])

    @sync
    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(CyclicDependencyOneExtension))
        with self.assertRaises(CyclicDependencyError):
            async with App(configuration) as sut:
                sut.extensions

    @sync
    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
        configuration.extensions.add(AppExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))
            self.assertEquals(NonConfigurableExtension, type(carrier[1]))

    @sync
    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))

    @sync
    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[1]))

    @sync
    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[0]))

    @sync
    async def test_extensions_addition_to_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_removal_from_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            del configuration.extensions[NonConfigurableExtension]
            self.assertNotIn(NonConfigurableExtension, sut.extensions)

    @sync
    async def test_assets_without_assets_directory_path(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(1, len(sut.assets.paths))

    @sync
    async def test_assets_with_assets_directory_path(self) -> None:
        assets_directory_path = Path('/tmp/betty')
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.assets_directory_path = assets_directory_path
        async with App(configuration) as sut:
            self.assertEquals(2, len(sut.assets.paths))
            self.assertEquals((assets_directory_path, None), sut.assets.paths[0])
