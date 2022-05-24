from typing import Type, Dict, Any

from parameterized import parameterized
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import Extension, App, ConfigurableExtension
from betty.config import Configuration as GenericConfiguration, Configurable, ConfigurationError, DumpedConfiguration
from betty.model import Entity, get_entity_type_name
from betty.project import ProjectExtensionConfiguration, ProjectExtensionsConfiguration, Configuration, \
    LocaleConfiguration, LocalesConfiguration, ThemeConfiguration, EntityReference, EntityReferences
from betty.tests import TestCase
from betty.typing import Void


class EntityReferenceTest(TestCase):
    def test_entity_type_with_constraint(self) -> None:
        entity_type = Entity
        sut = EntityReference(entity_type_constraint=entity_type)
        self.assertEqual(entity_type, sut.entity_type)
        with self.assertRaises(AttributeError):
            sut.entity_type = entity_type

    def test_entity_type_without_constraint(self) -> None:
        entity_type = Entity
        sut = EntityReference()
        self.assertIsNone(sut.entity_type)
        sut.entity_type = entity_type
        self.assertEqual(entity_type, sut.entity_type)

    def test_entity_id(self) -> None:
        entity_id = '123'
        sut = EntityReference()
        self.assertIsNone(sut.entity_id)
        sut.entity_id = entity_id
        self.assertEqual(entity_id, sut.entity_id)

    def test_load_with_constraint(self) -> None:
        entity_type_constraint = Entity
        sut = EntityReference(entity_type_constraint=entity_type_constraint)
        entity_id = '123'
        dumped_configuration = entity_id
        sut.load(dumped_configuration)
        self.assertEqual(entity_id, sut.entity_id)

    def test_load_with_constraint_without_string_should_error(self) -> None:
        entity_type_constraint = Entity
        sut = EntityReference(entity_type_constraint=entity_type_constraint)
        entity_id = None
        dumped_configuration = entity_id
        with App():
            with self.assertRaises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_load_without_constraint(self) -> None:
        sut = EntityReference()
        entity_type = Entity
        entity_id = '123'
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        sut.load(dumped_configuration)
        self.assertEqual(entity_type, sut.entity_type)
        self.assertEqual(entity_id, sut.entity_id)

    def test_load_without_constraint_without_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_id': entity_id,
        }
        with App():
            with self.assertRaises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_load_without_constraint_without_string_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_type': None,
            'entity_id': entity_id,
        }
        with self.assertRaises(ConfigurationError):
            sut.load(dumped_configuration)

    def test_load_without_constraint_without_importable_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_type': 'betty.non_existent.Entity',
            'entity_id': entity_id,
        }
        with self.assertRaises(ConfigurationError):
            sut.load(dumped_configuration)

    def test_load_without_constraint_without_entity_id_should_error(self) -> None:
        sut = EntityReference()
        entity_type = Entity
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
        }
        with App():
            with self.assertRaises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_load_without_constraint_without_string_entity_id_should_error(self) -> None:
        sut = EntityReference()
        entity_type = Entity
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': None,
        }
        with App():
            with self.assertRaises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_dump_with_constraint(self) -> None:
        sut = EntityReference(entity_type_constraint=Entity)
        entity_id = '123'
        sut.entity_id = entity_id
        expected = entity_id
        self.assertEqual(expected, sut.dump())

    def test_dump_without_constraint(self) -> None:
        sut = EntityReference()
        entity_type = Entity
        entity_id = '123'
        sut.entity_type = entity_type
        sut.entity_id = entity_id
        expected = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        self.assertEqual(expected, sut.dump())


class EntityReferencesTest(TestCase):
    @parameterized.expand([
        (EntityReferences(),),
        (EntityReferences(entity_type_constraint=Entity),),
    ])
    def test_load_without_list_should_error(self, sut: EntityReferences) -> None:
        dumped_configuration = None
        with App():
            with self.assertRaises(ConfigurationError):
                sut.load(dumped_configuration)

    @parameterized.expand([
        (EntityReferences(),),
        (EntityReferences(entity_type_constraint=Entity),),
    ])
    def test_load_without_entity_references(self, sut: EntityReferences) -> None:
        dumped_configuration: DumpedConfiguration = []
        sut.load(dumped_configuration)
        self.assertCountEqual([], sut)

    def test_load_with_constraint_with_entity_references(self) -> None:
        entity_type = Entity
        entity_id = '123'
        sut = EntityReferences(entity_type_constraint=entity_type)
        dumped_configuration = [
            entity_id,
        ]
        sut.load(dumped_configuration)
        self.assertCountEqual([EntityReference(entity_type, entity_id)], sut)

    def test_load_without_constraint_with_entity_references(self) -> None:
        sut = EntityReferences()
        entity_type = Entity
        entity_id = '123'
        dumped_configuration = [
            {
                'entity_type': get_entity_type_name(entity_type),
                'entity_id': entity_id,
            },
        ]
        sut.load(dumped_configuration)
        self.assertCountEqual([EntityReference(entity_type, entity_id)], sut)

    def test_dump_with_constraint_with_entity_references(self) -> None:
        entity_type = Entity
        entity_id = '123'
        sut = EntityReferences(entity_type_constraint=entity_type)
        sut.append(EntityReference(entity_type, entity_id))
        expected = [
            entity_id,
        ]
        self.assertEqual(expected, sut.dump())

    def test_dump_with_constraint_without_entity_references(self) -> None:
        sut = EntityReferences(entity_type_constraint=Entity)
        expected = Void
        self.assertEqual(expected, sut.dump())

    def test_dump_without_constraint_with_entity_references(self) -> None:
        entity_type = Entity
        entity_id = '123'
        sut = EntityReferences()
        sut.append(EntityReference(entity_type, entity_id))
        expected = [
            {
                'entity_type': get_entity_type_name(entity_type),
                'entity_id': entity_id,
            },
        ]
        self.assertEqual(expected, sut.dump())

    def test_dump_without_constraint_without_entity_references(self) -> None:
        sut = EntityReferences()
        expected = Void
        self.assertEqual(expected, sut.dump())


class LocaleConfigurationTest(TestCase):
    def test_locale(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        self.assertEqual(locale, sut.locale)

    def test_alias_implicit(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        self.assertEqual(locale, sut.alias)

    def test_alias_explicit(self):
        locale = 'nl-NL'
        alias = 'nl'
        sut = LocaleConfiguration(locale, alias)
        self.assertEqual(alias, sut.alias)

    @parameterized.expand([
        (False, LocaleConfiguration('nl', 'NL'), 'not a locale configuration'),
        (False, LocaleConfiguration('nl', 'NL'), 999),
        (False, LocaleConfiguration('nl', 'NL'), object()),
    ])
    def test_eq(self, expected, sut, other):
        self.assertEqual(expected, sut == other)


class LocalesConfigurationTest(TestCase):
    def test_getitem(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertEqual(locale_configuration_a, sut['nl-NL'])

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
        with App():
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
            self.assertEqual(2, len(sut))

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
            self.assertEqual(other, sut)

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
        self.assertEqual(LocaleConfiguration('en-US'), sut.default)

    def test_default_without_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
            locale_configuration_b,
        ])
        self.assertEqual(locale_configuration_a, sut.default)

    def test_default_with_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocalesConfiguration([
            locale_configuration_a,
        ])
        sut.default = locale_configuration_b
        self.assertEqual(locale_configuration_b, sut.default)


class _DummyExtension(Extension):
    @classmethod
    def label(cls) -> str:
        return 'Dummy'


class _DummyConfiguration(GenericConfiguration):
    pass


class _DummyConfigurableExtension(Extension, Configurable):
    @classmethod
    def label(cls) -> str:
        return 'Configurable dummy'

    @classmethod
    def configuration_type(cls) -> Type[_DummyConfiguration]:
        return _DummyConfiguration


class ProjectExtensionConfigurationTest(TestCase):
    def test_extension_type(self) -> None:
        extension_type = _DummyExtension
        sut = ProjectExtensionConfiguration(extension_type)
        self.assertEqual(extension_type, sut.extension_type)

    def test_enabled(self) -> None:
        enabled = True
        sut = ProjectExtensionConfiguration(_DummyExtension, enabled)
        self.assertEqual(enabled, sut.enabled)
        with assert_reactor_called(sut):
            sut.enabled = False

    def test_configuration(self) -> None:
        extension_type_configuration = GenericConfiguration()
        sut = ProjectExtensionConfiguration(Extension, True, extension_type_configuration)
        self.assertEqual(extension_type_configuration, sut.extension_configuration)
        with assert_reactor_called(sut):
            extension_type_configuration.react.trigger()

    @parameterized.expand([
        (True, ProjectExtensionConfiguration(_DummyExtension, True), ProjectExtensionConfiguration(_DummyExtension, True)),
        (True, ProjectExtensionConfiguration(_DummyExtension, True, None), ProjectExtensionConfiguration(_DummyExtension, True, None)),
        (False, ProjectExtensionConfiguration(_DummyExtension, True, GenericConfiguration()), ProjectExtensionConfiguration(_DummyExtension, True, GenericConfiguration())),
        (False, ProjectExtensionConfiguration(_DummyExtension, True), ProjectExtensionConfiguration(_DummyExtension, False)),
        (False, ProjectExtensionConfiguration(_DummyExtension, True), ProjectExtensionConfiguration(_DummyConfigurableExtension, True)),
    ])
    def test_eq(self, expected: bool, one: ProjectExtensionConfiguration, other: ProjectExtensionConfiguration) -> None:
        self.assertEqual(expected, one == other)


class ProjectExtensionsConfigurationTest(TestCase):
    def test_getitem(self) -> None:
        app_extension_configuration_a = ProjectExtensionConfiguration(DummyConfigurableExtension)
        sut = ProjectExtensionsConfiguration([
            app_extension_configuration_a,
        ])
        with assert_in_scope(sut):
            self.assertEqual(app_extension_configuration_a, sut[DummyConfigurableExtension])

    def test_delitem(self) -> None:
        app_extension_configuration = ProjectExtensionConfiguration(DummyConfigurableExtension)
        sut = ProjectExtensionsConfiguration([
            app_extension_configuration,
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[DummyConfigurableExtension]
        self.assertCountEqual([], sut)
        self.assertCountEqual([], app_extension_configuration.react._reactors)

    def test_iter(self) -> None:
        app_extension_configuration_a = ProjectExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = ProjectExtensionConfiguration(DummyNonConfigurableExtension)
        sut = ProjectExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertCountEqual([app_extension_configuration_a, app_extension_configuration_b], iter(sut))

    def test_len(self) -> None:
        app_extension_configuration_a = ProjectExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = ProjectExtensionConfiguration(DummyNonConfigurableExtension)
        sut = ProjectExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEqual(2, len(sut))

    def test_eq(self) -> None:
        app_extension_configuration_a = ProjectExtensionConfiguration(DummyConfigurableExtension)
        app_extension_configuration_b = ProjectExtensionConfiguration(DummyNonConfigurableExtension)
        sut = ProjectExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        other = ProjectExtensionsConfiguration([
            app_extension_configuration_a,
            app_extension_configuration_b,
        ])
        with assert_in_scope(sut):
            self.assertEqual(other, sut)

    def test_add(self) -> None:
        sut = ProjectExtensionsConfiguration()
        app_extension_configuration = ProjectExtensionConfiguration(DummyConfigurableExtension)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.add(app_extension_configuration)
        self.assertEqual(app_extension_configuration, sut[DummyConfigurableExtension])
        with assert_reactor_called(sut):
            app_extension_configuration.react.trigger()


class ThemeConfigurationTest(TestCase):
    def test_load_with_minimal_configuration(self) -> None:
        dumped_configuration: Dict = {}
        with App():
            ThemeConfiguration().load(dumped_configuration)

    def test_load_without_dict_should_error(self) -> None:
        dumped_configuration = None
        with App():
            with self.assertRaises(ConfigurationError):
                ThemeConfiguration().load(dumped_configuration)

    def test_dump_with_minimal_configuration(self) -> None:
        sut = ThemeConfiguration()
        expected = Void
        self.assertEqual(expected, sut.dump())

    def test_dump_with_background_image_id(self) -> None:
        sut = ThemeConfiguration()
        background_image_id = '123'
        sut.background_image.entity_id = background_image_id
        expected = {
            'background_image_id': background_image_id,
        }
        self.assertEqual(expected, sut.dump())

    def test_dump_with_featured_entities(self) -> None:
        sut = ThemeConfiguration()
        entity_type = Entity
        entity_id = '123'
        sut.featured_entities.append(EntityReference(entity_type, entity_id))
        expected = {
            'featured_entities': [
                {
                    'entity_type': get_entity_type_name(entity_type),
                    'entity_id': entity_id,
                },
            ],
        }
        self.assertEqual(expected, sut.dump())


class ConfigurationTest(TestCase):
    def test_base_url(self):
        sut = Configuration()
        base_url = 'https://example.com'
        sut.base_url = base_url
        self.assertEqual(base_url, sut.base_url)

    def test_base_url_without_scheme_should_error(self):
        sut = Configuration()
        with App():
            with self.assertRaises(ConfigurationError):
                sut.base_url = '/'

    def test_base_url_without_path_should_error(self):
        sut = Configuration()
        with App():
            with self.assertRaises(ConfigurationError):
                sut.base_url = 'file://'

    def test_root_path(self):
        sut = Configuration()
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        sut.root_path = configured_root_path
        self.assertEqual(expected_root_path, sut.root_path)

    def test_clean_urls(self):
        sut = Configuration()
        clean_urls = True
        sut.clean_urls = clean_urls
        self.assertEqual(clean_urls, sut.clean_urls)

    def test_content_negotiation(self):
        sut = Configuration()
        content_negotiation = True
        sut.content_negotiation = content_negotiation
        self.assertEqual(content_negotiation, sut.content_negotiation)

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
        self.assertEqual(author, sut.author)

    def test_load_should_load_minimal(self) -> None:
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(dumped_configuration['base_url'], configuration.base_url)
        self.assertEqual('Betty', configuration.title)
        self.assertIsNone(configuration.author)
        self.assertFalse(configuration.debug)
        self.assertEqual('', configuration.root_path)
        self.assertFalse(configuration.clean_urls)
        self.assertFalse(configuration.content_negotiation)

    def test_load_should_load_title(self) -> None:
        title = 'My first Betty site'
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['title'] = title
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(title, configuration.title)

    def test_load_should_load_author(self) -> None:
        author = 'Bart'
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['author'] = author
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(author, configuration.author)

    def test_load_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['locales'] = [locale_config]
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(LocalesConfiguration([LocaleConfiguration(locale)]), configuration.locales)

    def test_load_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['locales'] = [locale_config]
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(LocalesConfiguration([LocaleConfiguration(locale, alias)]), configuration.locales)

    def test_load_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['root_path'] = configured_root_path
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(expected_root_path, configuration.root_path)

    def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['clean_urls'] = clean_urls
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(clean_urls, configuration.clean_urls)

    def test_load_should_content_negotiation(self) -> None:
        content_negotiation = True
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['content_negotiation'] = content_negotiation
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(content_negotiation, configuration.content_negotiation)

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_load_should_load_debug(self, debug: bool) -> None:
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['debug'] = debug
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(debug, configuration.debug)

    def test_load_should_load_one_extension_with_configuration(self) -> None:
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
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
        expected = ProjectExtensionsConfiguration([
            ProjectExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
                check=1337,
            )),
        ])
        self.assertEqual(expected, configuration.extensions)

    def test_load_should_load_one_extension_without_configuration(self) -> None:
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['extensions'] = {
            DummyNonConfigurableExtension.name(): {},
        }
        configuration = Configuration()
        configuration.load(dumped_configuration)
        expected = ProjectExtensionsConfiguration([
            ProjectExtensionConfiguration(DummyNonConfigurableExtension, True),
        ])
        self.assertEqual(expected, configuration.extensions)

    def test_load_extension_with_invalid_configuration_should_raise_error(self):
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['extensions'] = {
            DummyConfigurableExtension.name(): 1337,
        }
        with App():
            with self.assertRaises(ConfigurationError):
                configuration = Configuration()
                configuration.load(dumped_configuration)

    def test_load_unknown_extension_type_name_should_error(self):
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['extensions'] = {
            'non.existent.type': None,
        }
        with self.assertRaises(ConfigurationError):
            configuration = Configuration()
            configuration.load(dumped_configuration)

    def test_load_not_an_extension_type_name_should_error(self):
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['extensions'] = {
            '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
        }
        with App():
            with self.assertRaises(ConfigurationError):
                configuration = Configuration()
                configuration.load(dumped_configuration)

    def test_load_should_load_theme_background_image_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        dumped_configuration: Any = self.assertIsNotVoid(Configuration().dump())
        dumped_configuration['theme'] = {
            'background_image_id': background_image_id
        }
        configuration = Configuration()
        configuration.load(dumped_configuration)
        self.assertEqual(background_image_id, configuration.theme.background_image.entity_id)

    def test_load_should_error_if_invalid_config(self) -> None:
        dumped_configuration: Dict = {}
        with App():
            with self.assertRaises(ConfigurationError):
                configuration = Configuration()
                configuration.load(dumped_configuration)

    def test_dump_should_dump_minimal(self) -> None:
        configuration = Configuration()
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(dumped_configuration['base_url'], configuration.base_url)
        self.assertEqual('Betty', configuration.title)
        self.assertIsNone(configuration.author)
        self.assertEqual(False, configuration.debug)
        self.assertEqual('', configuration.root_path)
        self.assertFalse(configuration.clean_urls)
        self.assertFalse(configuration.content_negotiation)

    def test_dump_should_dump_title(self) -> None:
        title = 'My first Betty site'
        configuration = Configuration()
        configuration.title = title
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(title, dumped_configuration['title'])

    def test_dump_should_dump_author(self) -> None:
        author = 'Bart'
        configuration = Configuration()
        configuration.author = author
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(author, dumped_configuration['author'])

    def test_dump_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        configuration = Configuration()
        configuration.locales.replace([locale_configuration])
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
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
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
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
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(root_path, dumped_configuration['root_path'])

    def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        configuration = Configuration()
        configuration.clean_urls = clean_urls
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(clean_urls, dumped_configuration['clean_urls'])

    def test_dump_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        configuration = Configuration()
        configuration.content_negotiation = content_negotiation
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(content_negotiation, dumped_configuration['content_negotiation'])

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_dump_should_dump_debug(self, debug: bool) -> None:
        configuration = Configuration()
        configuration.debug = debug
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(debug, dumped_configuration['debug'])

    def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        configuration = Configuration()
        configuration.extensions.add(ProjectExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
            check=1337,
        )))
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        expected = {
            DummyConfigurableExtension.name(): {
                'enabled': True,
                'configuration': {
                    'check': 1337,
                },
            },
        }
        self.assertEqual(expected, dumped_configuration['extensions'])

    def test_dump_should_dump_one_extension_without_configuration(self) -> None:
        configuration = Configuration()
        configuration.extensions.add(ProjectExtensionConfiguration(DummyNonConfigurableExtension))
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        expected = {
            DummyNonConfigurableExtension.name(): {
                'enabled': True,
            },
        }
        self.assertEqual(expected, dumped_configuration['extensions'])

    def test_dump_should_error_if_invalid_config(self) -> None:
        dumped_configuration: Dict = {}
        with App():
            with self.assertRaises(ConfigurationError):
                configuration = Configuration()
                configuration.load(dumped_configuration)

    def test_dump_should_dump_theme_background_image(self) -> None:
        background_image_id = 'my-favorite-picture'
        configuration = Configuration()
        configuration.theme.background_image.entity_id = background_image_id
        dumped_configuration: Any = self.assertIsNotVoid(configuration.dump())
        self.assertEqual(background_image_id, dumped_configuration['theme']['background_image_id'])


class DummyNonConfigurableExtension(Extension):
    pass  # pragma: no cover


class DummyConfigurableExtensionConfiguration(GenericConfiguration):
    def __init__(self, check):
        super().__init__()
        self.check = check

    @classmethod
    def default(cls) -> GenericConfiguration:
        return cls(False)

    def __eq__(self, other):
        return self.check == other.check and self.default == other.default

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError

        if 'check' not in dumped_configuration:
            raise ConfigurationError
        self.check = dumped_configuration['check']

    def dump(self) -> DumpedConfiguration:
        return {
            'check': self.check,
        }


class DummyConfigurableExtension(ConfigurableExtension[DummyConfigurableExtensionConfiguration]):
    @classmethod
    def default_configuration(cls) -> DummyConfigurableExtensionConfiguration:
        return DummyConfigurableExtensionConfiguration(False)
