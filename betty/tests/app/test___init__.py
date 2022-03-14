from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Type, List, Set

from parameterized import parameterized
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import Configuration, LocaleConfiguration, LocalesConfiguration, AppExtensionConfiguration, Extension, \
    AppExtensionsConfiguration, ConfigurationError, App, CyclicDependencyError
from betty.asyncio import sync
from betty.config import Configuration as GenericConfiguration, ConfigurationT, Configurable
from betty.model.ancestry import Ancestry
from betty.tests import TestCase


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


class _DummyExtension(Extension):
    @classmethod
    def label(cls) -> str:
        return 'Dummy'


class _DummyConfiguration(Configuration):
    pass


class _DummyConfigurableExtension(Extension, Configurable):
    @classmethod
    def label(cls) -> str:
        return 'Configurable dummy'

    @classmethod
    def configuration_type(cls) -> Type[ConfigurationT]:
        return _DummyConfiguration


class AppExtensionConfigurationTest(TestCase):
    def test_extension_type(self) -> None:
        extension_type = _DummyExtension
        sut = AppExtensionConfiguration(extension_type)
        self.assertEquals(extension_type, sut.extension_type)

    def test_enabled(self) -> None:
        enabled = True
        sut = AppExtensionConfiguration(_DummyExtension, enabled)
        self.assertEquals(enabled, sut.enabled)
        with assert_reactor_called(sut):
            sut.enabled = False

    def test_configuration(self) -> None:
        extension_type_configuration = GenericConfiguration()
        sut = AppExtensionConfiguration(Extension, True, extension_type_configuration)
        self.assertEquals(extension_type_configuration, sut.extension_configuration)
        with assert_reactor_called(sut):
            extension_type_configuration.react.trigger()

    @parameterized.expand([
        (True, AppExtensionConfiguration(_DummyExtension, True), AppExtensionConfiguration(_DummyExtension, True)),
        (True, AppExtensionConfiguration(_DummyExtension, True, None), AppExtensionConfiguration(_DummyExtension, True, None)),
        (False, AppExtensionConfiguration(_DummyExtension, True, GenericConfiguration()), AppExtensionConfiguration(_DummyExtension, True, GenericConfiguration())),
        (False, AppExtensionConfiguration(_DummyExtension, True), AppExtensionConfiguration(_DummyExtension, False)),
        (False, AppExtensionConfiguration(_DummyExtension, True), AppExtensionConfiguration(_DummyConfigurableExtension, True)),
    ])
    def test_eq(self, expected: bool, one: AppExtensionConfiguration, other: AppExtensionConfiguration) -> None:
        self.assertEqual(expected, one == other)


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
    def test_assets_directory_path_without_path(self):
        sut = Configuration()
        self.assertIsNone(sut.assets_directory_path)

    def test_assets_directory_path_with_path(self):
        sut = Configuration()
        assets_directory_path = '/tmp/betty-assets'
        sut.assets_directory_path = assets_directory_path
        self.assertEquals(assets_directory_path,
                          sut.assets_directory_path)

    def test_base_url(self):
        sut = Configuration()
        base_url = 'https://example.com'
        sut.base_url = base_url
        self.assertEquals(base_url, sut.base_url)

    def test_base_url_without_scheme_should_error(self):
        sut = Configuration()
        with self.assertRaises(ConfigurationError):
            sut.base_url = '/'

    def test_base_url_without_path_should_error(self):
        sut = Configuration()
        with self.assertRaises(ConfigurationError):
            sut.base_url = 'file://'

    def test_root_path(self):
        sut = Configuration()
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        sut.root_path = configured_root_path
        self.assertEquals(expected_root_path, sut.root_path)

    def test_clean_urls(self):
        sut = Configuration()
        clean_urls = True
        sut.clean_urls = clean_urls
        self.assertEquals(clean_urls, sut.clean_urls)

    def test_content_negotiation(self):
        sut = Configuration()
        content_negotiation = True
        sut.content_negotiation = content_negotiation
        self.assertEquals(content_negotiation, sut.content_negotiation)

    def test_clean_urls_implied_by_content_negotiation(self):
        sut = Configuration()
        sut.content_negotiation = True
        self.assertTrue(sut.clean_urls)

    def test_author_without_author(self):
        sut = Configuration()
        self.assertIsNone(sut.author)

    def test_author_with_author(self):
        sut = Configuration()
        author = 'Bart'
        sut.author = author
        self.assertEquals(author, sut.author)

    def test_load_should_load_minimal(self) -> None:
        dumped_configuration = Configuration().dump()
        configuration = Configuration()
        configuration.load(dumped_configuration)
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
        dumped_configuration = Configuration().dump()
        dumped_configuration['title'] = title
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(title, configuration.title)

    def test_load_should_load_author(self) -> None:
        author = 'Bart'
        dumped_configuration = Configuration().dump()
        dumped_configuration['author'] = author
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(author, configuration.author)

    def test_load_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        dumped_configuration = Configuration().dump()
        dumped_configuration['locales'] = [locale_config]
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(LocalesConfiguration([LocaleConfiguration(locale)]), configuration.locales)

    def test_load_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        dumped_configuration = Configuration().dump()
        dumped_configuration['locales'] = [locale_config]
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(LocalesConfiguration([LocaleConfiguration(locale, alias)]), configuration.locales)

    def test_load_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        dumped_configuration = Configuration().dump()
        dumped_configuration['root_path'] = configured_root_path
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(expected_root_path, configuration.root_path)

    def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        dumped_configuration = Configuration().dump()
        dumped_configuration['clean_urls'] = clean_urls
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(clean_urls, configuration.clean_urls)

    def test_load_should_content_negotiation(self) -> None:
        content_negotiation = True
        dumped_configuration = Configuration().dump()
        dumped_configuration['content_negotiation'] = content_negotiation
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_load_should_load_debug(self, debug: bool) -> None:
        dumped_configuration = Configuration().dump()
        dumped_configuration['debug'] = debug
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(debug, configuration.debug)

    def test_load_should_load_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            dumped_configuration = Configuration().dump()
            dumped_configuration['assets'] = assets_directory_path
            configuration = Configuration()
            configuration.load(dumped_configuration)
            self.assertEquals(Path(assets_directory_path).expanduser().resolve(), configuration.assets_directory_path)

    def test_load_should_load_one_extension_with_configuration(self) -> None:
        dumped_configuration = Configuration().dump()
        extension_configuration = {
            'check': 1337,
        }
        dumped_configuration['extensions'] = {
            DummyConfigurableExtension.name(): {
                'configuration': extension_configuration,
            },
        }
        configuration = Configuration()
        configuration.load(dumped_configuration)
        expected = AppExtensionsConfiguration([
            AppExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
                check=1337,
                default='I will always be there for you.',
            )),
        ])
        self.assertEquals(expected, configuration.extensions)

    def test_load_should_load_one_extension_without_configuration(self) -> None:
        dumped_configuration = Configuration().dump()
        dumped_configuration['extensions'] = {
            DummyNonConfigurableExtension.name(): {},
        }
        configuration = Configuration()
        configuration.load(dumped_configuration)
        expected = AppExtensionsConfiguration([
            AppExtensionConfiguration(DummyNonConfigurableExtension, True),
        ])
        self.assertEquals(expected, configuration.extensions)

    def test_load_extension_with_invalid_configuration_should_raise_error(self):
        dumped_configuration = Configuration().dump()
        dumped_configuration['extensions'] = {
            DummyConfigurableExtension.name(): 1337,
        }
        with self.assertRaises(ConfigurationError):
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_load_unknown_extension_type_name_should_error(self):
        dumped_configuration = Configuration().dump()
        dumped_configuration['extensions'] = {
            'non.existent.type': None,
        }
        with self.assertRaises(ConfigurationError):
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_load_not_an_extension_type_name_should_error(self):
        dumped_configuration = Configuration().dump()
        dumped_configuration['extensions'] = {
            '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
        }
        with self.assertRaises(ConfigurationError):
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_load_should_load_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        dumped_configuration = Configuration().dump()
        dumped_configuration['theme'] = {
            'background_image_id': background_image_id
        }
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEquals(background_image_id, configuration.theme.background_image_id)

    def test_load_should_error_if_invalid_config(self) -> None:
        dumped_configuration = {}
        with self.assertRaises(ConfigurationError):
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_dump_should_dump_minimal(self) -> None:
        configuration = Configuration()
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
        configuration = Configuration()
        configuration.title = title
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(title, dumped_configuration['title'])

    def test_dump_should_dump_author(self) -> None:
        author = 'Bart'
        configuration = Configuration()
        configuration.author = author
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(author, dumped_configuration['author'])

    def test_dump_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        configuration = Configuration()
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
        configuration = Configuration()
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
        configuration = Configuration()
        configuration.root_path = root_path
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(root_path, dumped_configuration['root_path'])

    def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        configuration = Configuration()
        configuration.clean_urls = clean_urls
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(clean_urls, dumped_configuration['clean_urls'])

    def test_dump_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        configuration = Configuration()
        configuration.content_negotiation = content_negotiation
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(content_negotiation, dumped_configuration['content_negotiation'])

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_dump_should_dump_debug(self, debug: bool) -> None:
        configuration = Configuration()
        configuration.debug = debug
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(debug, dumped_configuration['debug'])

    def test_dump_should_dump_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            configuration = Configuration()
            configuration.assets_directory_path = assets_directory_path
            dumped_configuration = Configuration.dump(configuration)
            self.assertEquals(assets_directory_path, dumped_configuration['assets'])

    def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        configuration = Configuration()
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
        configuration = Configuration()
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
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_dump_should_dump_theme_background_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        configuration = Configuration()
        configuration.theme.background_image_id = background_image_id
        dumped_configuration = Configuration.dump(configuration)
        self.assertEquals(background_image_id, dumped_configuration['theme']['background_image_id'])


class DummyNonConfigurableExtension(Extension):
    pass  # pragma: no cover


class DummyConfigurableExtensionConfiguration(GenericConfiguration):
    def __init__(self, check, default='I will always be there for you.'):
        super().__init__()
        self.check = check
        self.default = default

    @classmethod
    def default(cls) -> GenericConfiguration:
        return cls(False)

    def __eq__(self, other):
        return self.check == other.check and self.default == other.default

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError

        if 'check' not in dumped_configuration:
            raise ConfigurationError
        self.check = dumped_configuration['check']

        if 'default' in dumped_configuration:
            self.default = dumped_configuration['default']

    def dump(self) -> Any:
        return {
            'check': self.check,
            'default': self.default,
        }


class DummyConfigurableExtension(Extension, Configurable):
    @classmethod
    def configuration_type(cls) -> Type[GenericConfiguration]:
        return DummyConfigurableExtensionConfiguration


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
    def default(cls) -> Configuration:
        return cls(False)

    def load(self, dumped_configuration: Any) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError
        if 'check' not in dumped_configuration:
            raise ConfigurationError
        self.check = dumped_configuration['check']

    def dump(self) -> Any:
        return {
            'check': self.check
        }


class ConfigurableExtension(Extension, Configurable):
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
        async with App() as sut:
            self.assertIsInstance(sut.ancestry, Ancestry)

    @sync
    async def test_extensions_with_one_extension(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_with_one_configurable_extension(self) -> None:
        check = 1337
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
                check=check,
            )))
            self.assertIsInstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
            self.assertEquals(check, sut.extensions[ConfigurableExtension]._configuration.check)

    @sync
    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
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
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
            sut.configuration.extensions.add(AppExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
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
        with self.assertRaises(CyclicDependencyError):
            async with App() as sut:
                sut.configuration.extensions.add(AppExtensionConfiguration(CyclicDependencyOneExtension))
                sut.extensions

    @sync
    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            sut.configuration.extensions.add(AppExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))
            self.assertEquals(NonConfigurableExtension, type(carrier[1]))

    @sync
    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))

    @sync
    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            sut.configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[1]))

    @sync
    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[0]))

    @sync
    async def test_extensions_addition_to_configuration(self) -> None:
        async with App() as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            sut.configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_removal_from_configuration(self) -> None:
        async with App() as sut:
            sut.configuration.extensions.add(AppExtensionConfiguration(NonConfigurableExtension))
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            del sut.configuration.extensions[NonConfigurableExtension]
            self.assertNotIn(NonConfigurableExtension, sut.extensions)

    @sync
    async def test_assets_without_assets_directory_path(self) -> None:
        async with App() as sut:
            self.assertEquals(1, len(sut.assets))

    @sync
    async def test_assets_with_assets_directory_path(self) -> None:
        with TemporaryDirectory() as assets_directory_path:
            async with App() as sut:
                sut.configuration.assets_directory_path = assets_directory_path
                self.assertEquals(2, len(sut.assets))
                self.assertEquals((Path(assets_directory_path), None), sut.assets.paths[0])
