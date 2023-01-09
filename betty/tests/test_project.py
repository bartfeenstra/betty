from __future__ import annotations

from typing import Type, Dict, Any

import pytest
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import Extension, App, ConfigurableExtension
from betty.config import Configuration, Configurable, DumpedConfigurationImport, DumpedConfigurationExport, \
    ConfigurationMapping
from betty.config.load import ConfigurationValidationError, Loader
from betty.model import Entity, get_entity_type_name, get_entity_type, UserFacingEntity
from betty.project import ExtensionConfiguration, ExtensionConfigurationMapping, ProjectConfiguration, \
    LocaleConfiguration, LocaleConfigurationCollection, EntityReference, EntityReferenceCollection, \
    EntityTypeConfiguration, EntityTypeConfigurationMapping
from betty.tests.config.test___init__ import raises_no_configuration_errors, raises_configuration_error, \
    ConfigurationCollectionMappingTestBase
from betty.typing import Void


class EntityReferenceTestEntity(Entity):
    pass


class TestEntityReference:
    def test_entity_type_with_constraint(self) -> None:
        entity_type = EntityReferenceTestEntity
        sut = EntityReference(entity_type_constraint=entity_type)
        assert entity_type == sut.entity_type
        with pytest.raises(AttributeError):
            sut.entity_type = entity_type

    def test_entity_type_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntity
        sut = EntityReference()
        assert sut.entity_type is None
        sut.entity_type = entity_type
        assert entity_type == sut.entity_type

    def test_entity_id(self) -> None:
        entity_id = '123'
        sut = EntityReference()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert entity_id == sut.entity_id

    def test_load_with_constraint(self) -> None:
        entity_type_constraint = EntityReferenceTestEntity
        sut = EntityReference(entity_type_constraint=entity_type_constraint)
        entity_id = '123'
        dumped_configuration = entity_id
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert entity_id == sut.entity_id

    def test_load_with_constraint_without_string_should_error(self) -> None:
        entity_type_constraint = EntityReferenceTestEntity
        sut = EntityReference(entity_type_constraint=entity_type_constraint)
        entity_id = None
        dumped_configuration = entity_id
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_without_constraint(self) -> None:
        sut = EntityReference()
        entity_type = EntityReferenceTestEntity
        entity_id = '123'
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert entity_type == sut.entity_type
        assert entity_id == sut.entity_id

    def test_load_without_constraint_without_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_id': entity_id,
        }
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_without_constraint_without_string_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_type': None,
            'entity_id': entity_id,
        }
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_without_constraint_without_importable_entity_type_should_error(self) -> None:
        sut = EntityReference()
        entity_id = '123'
        dumped_configuration = {
            'entity_type': 'betty.non_existent.Entity',
            'entity_id': entity_id,
        }
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_without_constraint_without_entity_id_should_error(self) -> None:
        sut = EntityReference()
        entity_type = EntityReferenceTestEntity
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
        }
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_without_constraint_without_string_entity_id_should_error(self) -> None:
        sut = EntityReference()
        entity_type = EntityReferenceTestEntity
        dumped_configuration = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': None,
        }
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_dump_with_constraint(self) -> None:
        sut = EntityReference(entity_type_constraint=Entity)
        entity_id = '123'
        sut.entity_id = entity_id
        expected = entity_id
        assert expected == sut.dump()

    def test_dump_without_constraint(self) -> None:
        sut = EntityReference()
        entity_type = EntityReferenceTestEntity
        entity_id = '123'
        sut.entity_type = entity_type
        sut.entity_id = entity_id
        expected = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        assert expected == sut.dump()


class EntityReferenceCollectionTestEntity(Entity):
    pass


class TestEntityReferenceCollection:
    @pytest.mark.parametrize('sut', [
        EntityReferenceCollection(),
        EntityReferenceCollection(entity_type_constraint=EntityReferenceCollectionTestEntity),
    ])
    def test_load_without_list_should_error(self, sut: EntityReferenceCollection) -> None:
        dumped_configuration = None
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    @pytest.mark.parametrize('sut', [
        EntityReferenceCollection(),
        EntityReferenceCollection(entity_type_constraint=EntityReferenceCollectionTestEntity),
    ])
    def test_load_without_entity_references(self, sut: EntityReferenceCollection) -> None:
        dumped_configuration: DumpedConfigurationImport = []
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert [] == list(sut)

    def test_load_with_constraint_with_entity_references(self) -> None:
        entity_type = EntityReferenceCollectionTestEntity
        entity_id = '123'
        sut = EntityReferenceCollection(entity_type_constraint=entity_type)
        dumped_configuration = [
            entity_id,
        ]
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert [EntityReference(entity_type, entity_id)] == list(sut)

    def test_load_without_constraint_with_entity_references(self) -> None:
        sut = EntityReferenceCollection()
        entity_type = EntityReferenceCollectionTestEntity
        entity_id = '123'
        dumped_configuration = [
            {
                'entity_type': get_entity_type_name(entity_type),
                'entity_id': entity_id,
            },
        ]
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert [EntityReference(entity_type, entity_id)] == list(sut)

    def test_dump_with_constraint_with_entity_references(self) -> None:
        entity_type = EntityReferenceCollectionTestEntity
        entity_id = '123'
        sut = EntityReferenceCollection(entity_type_constraint=entity_type)
        sut.append(EntityReference(entity_type, entity_id))
        expected = [
            entity_id,
        ]
        assert expected == sut.dump()

    def test_dump_with_constraint_without_entity_references(self) -> None:
        sut = EntityReferenceCollection(entity_type_constraint=EntityReferenceCollectionTestEntity)
        expected = Void
        assert expected == sut.dump()

    def test_dump_without_constraint_with_entity_references(self) -> None:
        entity_type = EntityReferenceCollectionTestEntity
        entity_id = '123'
        sut = EntityReferenceCollection()
        sut.append(EntityReference(entity_type, entity_id))
        expected = [
            {
                'entity_type': get_entity_type_name(entity_type),
                'entity_id': entity_id,
            },
        ]
        assert expected == sut.dump()

    def test_dump_without_constraint_without_entity_references(self) -> None:
        sut = EntityReferenceCollection()
        expected = Void
        assert expected == sut.dump()


class TestLocaleConfiguration:
    def test_locale(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        assert locale == sut.locale

    def test_alias_implicit(self):
        locale = 'nl-NL'
        sut = LocaleConfiguration(locale)
        assert locale == sut.alias

    def test_alias_explicit(self):
        locale = 'nl-NL'
        alias = 'nl'
        sut = LocaleConfiguration(locale, alias)
        assert alias == sut.alias

    def test_invalid_alias(self):
        locale = 'nl-NL'
        alias = '/'
        with pytest.raises(ConfigurationValidationError):
            with App():
                LocaleConfiguration(locale, alias)

    @pytest.mark.parametrize('expected, sut, other', [
        (False, LocaleConfiguration('nl', 'NL'), 'not a locale configuration'),
        (False, LocaleConfiguration('nl', 'NL'), 999),
        (False, LocaleConfiguration('nl', 'NL'), object()),
    ])
    def test_eq(self, expected, sut, other):
        assert expected == (sut == other)


class TestLocalesConfiguration:
    def test_getitem(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            assert locale_configuration_a == sut['nl-NL']

    def test_delitem(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['nl-NL']
        assert [locale_configuration_b] == list(sut)

    def test_delitem_with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
        ])
        with App():
            with pytest.raises(ConfigurationValidationError):
                del sut['nl-NL']

    def test_iter(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            assert [locale_configuration_a, locale_configuration_b] == list(iter(sut))

    def test_len(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            assert 2 == len(sut)

    def test_eq(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        other = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        with assert_in_scope(sut):
            assert other == sut

    def test_contains(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            assert 'nl-NL' in sut
            assert 'en-US' not in sut

    def test_repr(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
        ])
        with assert_in_scope(sut):
            assert isinstance(repr(sut), str)

    def test_add(self) -> None:
        sut = LocaleConfigurationCollection()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.add(LocaleConfiguration('nl-NL'))

    def test_default_without_explicit_locale_configurations(self):
        sut = LocaleConfigurationCollection()
        assert LocaleConfiguration('en-US') == sut.default

    def test_default_without_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
            locale_configuration_b,
        ])
        assert locale_configuration_a == sut.default

    def test_default_with_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationCollection([
            locale_configuration_a,
        ])
        sut.default = locale_configuration_b
        assert locale_configuration_b == sut.default


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
    def configuration_type(cls) -> Type[_DummyConfiguration]:
        return _DummyConfiguration


class TestExtensionConfiguration:
    def test_extension_type(self) -> None:
        extension_type = _DummyExtension
        sut = ExtensionConfiguration(extension_type)
        assert extension_type == sut.extension_type

    def test_enabled(self) -> None:
        enabled = True
        sut = ExtensionConfiguration(_DummyExtension, enabled)
        assert enabled == sut.enabled
        with assert_reactor_called(sut):
            sut.enabled = False

    def test_configuration(self) -> None:
        extension_type_configuration = Configuration()
        sut = ExtensionConfiguration(Extension, True, extension_type_configuration)
        assert extension_type_configuration == sut.extension_configuration
        with assert_reactor_called(sut):
            extension_type_configuration.react.trigger()

    @pytest.mark.parametrize('expected, one, other', [
        (True, ExtensionConfiguration(_DummyExtension, True), ExtensionConfiguration(_DummyExtension, True)),
        (True, ExtensionConfiguration(_DummyExtension, True, None), ExtensionConfiguration(_DummyExtension, True, None)),
        (False, ExtensionConfiguration(_DummyExtension, True, Configuration()), ExtensionConfiguration(_DummyExtension, True, Configuration())),
        (False, ExtensionConfiguration(_DummyExtension, True), ExtensionConfiguration(_DummyExtension, False)),
        (False, ExtensionConfiguration(_DummyExtension, True), ExtensionConfiguration(_DummyConfigurableExtension, True)),
    ])
    def test_eq(self, expected: bool, one: ExtensionConfiguration, other: ExtensionConfiguration) -> None:
        assert expected == (one == other)


class TestExtensionConfigurationMapping(ConfigurationCollectionMappingTestBase):
    def get_sut(self) -> ConfigurationMapping:
        return ExtensionConfigurationMapping()

    def get_configuration_key(self) -> Any:
        return DummyConfigurableExtension


class EntityTypeConfigurationTestEntityOne(UserFacingEntity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity):
    pass


class TestEntityTypeConfiguration:
    def test_entity_type(self) -> None:
        entity_type = EntityTypeConfigurationTestEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert entity_type == sut.entity_type

    @pytest.mark.parametrize('generate_html_list,', [
        True,
        False,
    ])
    def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        with assert_reactor_called(sut):
            sut.generate_html_list = generate_html_list
        assert generate_html_list == sut.generate_html_list

    def test_load_with_minimal_configuration(self) -> None:
        dumped_configuration: DumpedConfigurationImport = {}
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)

    @pytest.mark.parametrize('generate_html_list,', [
        True,
        False,
    ])
    def test_load_with_generate_html_list(self, generate_html_list: bool) -> None:
        dumped_configuration = {
            'generate_html_list': generate_html_list,
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
            loader.commit()
        assert generate_html_list == sut.generate_html_list

    def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = Void
        assert expected == sut.dump()

    def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, False)
        expected = {
            'generate_html_list': False,
        }
        assert expected == sut.dump()

    @pytest.mark.parametrize('expected, one, other', [
        (True, EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, True), EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, True)),
        (False, EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, True), EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, False)),
        (False, EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, True), EntityTypeConfiguration(EntityTypeConfigurationTestEntityOther, True)),
    ])
    def test_eq(self, expected: bool, one: EntityTypeConfiguration, other: EntityTypeConfiguration) -> None:
        assert expected == (one == other)


class EntityTypeConfigurationMappingTestEntity(UserFacingEntity, Entity):
    pass


class TestEntityTypeConfigurationMapping(ConfigurationCollectionMappingTestBase):
    def get_sut(self) -> ConfigurationMapping:
        return EntityTypeConfigurationMapping()

    def get_configuration_key(self) -> Any:
        return get_entity_type(EntityTypeConfigurationMappingTestEntity)


class TestProjectConfiguration:
    def test_base_url(self):
        sut = ProjectConfiguration()
        base_url = 'https://example.com'
        sut.base_url = base_url
        assert base_url == sut.base_url

    def test_base_url_without_scheme_should_error(self):
        sut = ProjectConfiguration()
        with App():
            with pytest.raises(ConfigurationValidationError):
                sut.base_url = '/'

    def test_base_url_without_path_should_error(self):
        sut = ProjectConfiguration()
        with App():
            with pytest.raises(ConfigurationValidationError):
                sut.base_url = 'file://'

    def test_root_path(self):
        sut = ProjectConfiguration()
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        sut.root_path = configured_root_path
        assert expected_root_path == sut.root_path

    def test_clean_urls(self):
        sut = ProjectConfiguration()
        clean_urls = True
        sut.clean_urls = clean_urls
        assert clean_urls == sut.clean_urls

    def test_content_negotiation(self):
        sut = ProjectConfiguration()
        content_negotiation = True
        sut.content_negotiation = content_negotiation
        assert content_negotiation == sut.content_negotiation

    def test_clean_urls_implied_by_content_negotiation(self):
        sut = ProjectConfiguration()
        sut.content_negotiation = True
        assert sut.clean_urls

    def test_author_without_author(self):
        sut = ProjectConfiguration()
        assert sut.author is None

    def test_author_with_author(self):
        sut = ProjectConfiguration()
        author = 'Bart'
        sut.author = author
        assert author == sut.author

    def test_load_should_load_minimal(self) -> None:
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert dumped_configuration['base_url'] == sut.base_url
        assert 'Betty' == sut.title
        assert sut.author is None
        assert not sut.debug
        assert '' == sut.root_path
        assert not sut.clean_urls
        assert not sut.content_negotiation

    def test_load_should_load_title(self) -> None:
        title = 'My first Betty site'
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['title'] = title
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert title == sut.title

    def test_load_should_load_author(self) -> None:
        author = 'Bart'
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['author'] = author
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert author == sut.author

    def test_load_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config = {
            'locale': locale,
        }
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['locales'] = [locale_config]
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert LocaleConfigurationCollection([LocaleConfiguration(locale)]) == sut.locales

    def test_load_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'locale': locale,
            'alias': alias,
        }
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['locales'] = [locale_config]
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert LocaleConfigurationCollection([LocaleConfiguration(locale, alias)]) == sut.locales

    def test_load_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['root_path'] = configured_root_path
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert expected_root_path == sut.root_path

    def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['clean_urls'] = clean_urls
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert clean_urls == sut.clean_urls

    def test_load_should_content_negotiation(self) -> None:
        content_negotiation = True
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['content_negotiation'] = content_negotiation
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert content_negotiation == sut.content_negotiation

    @pytest.mark.parametrize('debug', [
        True,
        False,
    ])
    def test_load_should_load_debug(self, debug: bool) -> None:
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['debug'] = debug
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        assert debug == sut.debug

    def test_load_should_load_one_extension_with_configuration(self) -> None:
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        extension_configuration = {
            'check': 1337,
        }
        dumped_configuration['extensions'] = {
            DummyConfigurableExtension.name(): {
                'configuration': extension_configuration,
            },
        }
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        expected = ExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
            check=1337,
        ))
        assert expected == sut.extensions[DummyConfigurableExtension]

    def test_load_should_load_one_extension_without_configuration(self) -> None:
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['extensions'] = {
            DummyNonConfigurableExtension.name(): {},
        }
        sut = ProjectConfiguration()
        with raises_no_configuration_errors() as loader:
            sut.load(dumped_configuration, loader)
        expected = ExtensionConfiguration(DummyNonConfigurableExtension, True)
        assert expected == sut.extensions[DummyNonConfigurableExtension]

    def test_load_extension_with_invalid_configuration_should_raise_error(self):
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['extensions'] = {
            DummyConfigurableExtension.name(): 1337,
        }
        sut = ProjectConfiguration()
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_unknown_extension_type_name_should_error(self):
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['extensions'] = {
            'non.existent.type': None,
        }
        sut = ProjectConfiguration()
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_not_an_extension_type_name_should_error(self):
        dumped_configuration: Any = ProjectConfiguration().dump()
        assert dumped_configuration is not Void
        dumped_configuration['extensions'] = {
            '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
        }
        sut = ProjectConfiguration()
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_load_should_error_if_invalid_config(self) -> None:
        dumped_configuration: Dict = {}
        sut = ProjectConfiguration()
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)

    def test_dump_should_dump_minimal(self) -> None:
        sut = ProjectConfiguration()
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert dumped_configuration['base_url'] == sut.base_url
        assert 'Betty' == sut.title
        assert sut.author is None
        assert not sut.debug
        assert '' == sut.root_path
        assert not sut.clean_urls
        assert not sut.content_negotiation

    def test_dump_should_dump_title(self) -> None:
        title = 'My first Betty site'
        sut = ProjectConfiguration()
        sut.title = title
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert title == dumped_configuration['title']

    def test_dump_should_dump_author(self) -> None:
        author = 'Bart'
        sut = ProjectConfiguration()
        sut.author = author
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert author == dumped_configuration['author']

    def test_dump_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration()
        sut.locales.replace([locale_configuration])
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert [
            {
                'locale': locale,
            },
        ] == dumped_configuration['locales']

    def test_dump_should_dump_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_configuration = LocaleConfiguration(locale, alias)
        sut = ProjectConfiguration()
        sut.locales.replace([locale_configuration])
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert [
            {
                'locale': locale,
                'alias': alias,
            },
        ] == dumped_configuration['locales']

    def test_dump_should_dump_root_path(self) -> None:
        root_path = 'betty'
        sut = ProjectConfiguration()
        sut.root_path = root_path
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert root_path == dumped_configuration['root_path']

    def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        sut = ProjectConfiguration()
        sut.clean_urls = clean_urls
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert clean_urls == dumped_configuration['clean_urls']

    def test_dump_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        sut = ProjectConfiguration()
        sut.content_negotiation = content_negotiation
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert content_negotiation == dumped_configuration['content_negotiation']

    @pytest.mark.parametrize('debug', [
        True,
        False,
    ])
    def test_dump_should_dump_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration()
        sut.debug = debug
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        assert debug == dumped_configuration['debug']

    def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.add(ExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration(
            check=1337,
        )))
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        expected = {
            'enabled': True,
            'configuration': {
                'check': 1337,
            },
        }
        assert expected == dumped_configuration['extensions'][DummyConfigurableExtension.name()]

    def test_dump_should_dump_one_extension_without_configuration(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.add(ExtensionConfiguration(DummyNonConfigurableExtension))
        dumped_configuration: Any = sut.dump()
        assert dumped_configuration is not Void
        expected = {
            'enabled': True,
        }
        assert expected == dumped_configuration['extensions'][DummyNonConfigurableExtension.name()]

    def test_dump_should_error_if_invalid_config(self) -> None:
        dumped_configuration: Dict = {}
        sut = ProjectConfiguration()
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            sut.load(dumped_configuration, loader)


class DummyNonConfigurableExtension(Extension):
    pass


class DummyConfigurableExtensionConfiguration(Configuration):
    def __init__(self, check):
        super().__init__()
        self.check = check

    @classmethod
    def default(cls) -> Configuration:
        return cls(False)

    def __eq__(self, other):
        return self.check == other.check and self.default == other.default

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        with loader.assert_required_key(
            dumped_configuration,
            'check',
            loader.assert_int,  # type: ignore
        ) as (dumped_check, valid):
            if valid:
                loader.assert_setattr(self, 'check', dumped_check)

    def dump(self) -> DumpedConfigurationExport:
        return {
            'check': self.check,
        }


class DummyConfigurableExtension(ConfigurableExtension[DummyConfigurableExtensionConfiguration]):
    @classmethod
    def default_configuration(cls) -> DummyConfigurableExtensionConfiguration:
        return DummyConfigurableExtensionConfiguration(False)
