from __future__ import annotations

from typing import Type, Dict, Any, Optional, Iterable, Tuple

import dill as pickle
import pytest
from reactives.tests import assert_reactor_called, assert_scope_empty

from betty.app import Extension, ConfigurableExtension
from betty.config import Configuration, Configurable
from betty.locale import Localizer
from betty.model import Entity, get_entity_type_name, UserFacingEntity
from betty.project import ExtensionConfiguration, ExtensionConfigurationMapping, ProjectConfiguration, \
    LocaleConfiguration, LocaleConfigurationMapping, EntityReference, EntityReferenceSequence, \
    EntityTypeConfiguration, EntityTypeConfigurationMapping
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import ValidationError, Asserter, Fields, Assertions, RequiredField
from betty.tests.serde import raises_error
from betty.tests.test_config import ConfigurationMappingTestBase, ConfigurationSequenceTestBase

try:
    from typing_extensions import Self
except ModuleNotFoundError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover


class EntityReferenceTestEntityOne(Entity):
    pass


class EntityReferenceTestEntityTwo(Entity):
    pass


class TestEntityReference:
    def test_entity_type_with_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](entity_type, None, entity_type_is_constrained=True)
        assert entity_type == sut.entity_type
        with pytest.raises(AttributeError):
            sut.entity_type = entity_type

    def test_entity_type_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_type is None
        sut.entity_type = entity_type
        assert entity_type == sut.entity_type

    def test_entity_id(self) -> None:
        entity_id = '123'
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert entity_id == sut.entity_id

    def test_load_with_constraint(self) -> None:
        configuration = EntityReference(EntityReferenceTestEntityOne, entity_type_is_constrained=True)
        entity_id = '123'
        dump = entity_id
        sut = EntityReference[EntityReferenceTestEntityOne].load(dump, configuration)
        assert entity_id == sut.entity_id

    @pytest.mark.parametrize('dump', [
        {
            'entity_type': EntityReferenceTestEntityOne,
            'entity_id': '123',
        },
        {
            'entity_type': EntityReferenceTestEntityTwo,
            'entity_id': '123',
        },
        False,
        123,
    ])
    def test_load_with_constraint_without_string_should_error(self, dump: Dump) -> None:
        configuration = EntityReference(EntityReferenceTestEntityOne, entity_type_is_constrained=True)
        with raises_error(error_type=ValidationError):
            EntityReference.load(dump, configuration)

    def test_load_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        entity_id = '123'
        dump: Dump = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne].load(dump)
        assert entity_type == sut.entity_type
        assert entity_id == sut.entity_id

    def test_load_without_constraint_without_entity_type_should_error(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_id = '123'
        dump: Dump = {
            'entity_id': entity_id,
        }
        with raises_error(error_type=ValidationError):
            EntityReference.load(dump, sut)

    def test_load_without_constraint_without_string_entity_type_should_error(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_id = '123'
        dump: Dump = {
            'entity_type': None,
            'entity_id': entity_id,
        }
        with raises_error(error_type=ValidationError):
            EntityReference.load(dump, sut)

    def test_load_without_constraint_without_importable_entity_type_should_error(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_id = '123'
        dump: Dump = {
            'entity_type': 'betty.non_existent.Entity',
            'entity_id': entity_id,
        }
        with raises_error(error_type=ValidationError):
            EntityReference.load(dump, sut)

    def test_load_without_constraint_without_string_entity_id_should_error(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_type = EntityReferenceTestEntityOne
        dump: Dump = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': None,
        }
        with raises_error(error_type=ValidationError):
            EntityReference.load(dump, sut)

    def test_dump_with_constraint(self) -> None:
        sut = EntityReference[Entity](Entity, None, entity_type_is_constrained=True)
        entity_id = '123'
        sut.entity_id = entity_id
        expected = entity_id
        assert expected == sut.dump()

    def test_dump_without_constraint(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_type = EntityReferenceTestEntityOne
        entity_id = '123'
        sut.entity_type = entity_type
        sut.entity_id = entity_id
        expected = {
            'entity_type': get_entity_type_name(entity_type),
            'entity_id': entity_id,
        }
        assert expected == sut.dump()


class EntityReferenceSequenceTestEntity(Entity):
    pass


class TestEntityReferenceSequence(ConfigurationSequenceTestBase):
    _ConfigurationT = EntityReference

    def get_sut(self, entity_references: Iterable[EntityReference] | None = None) -> EntityReferenceSequence:
        return EntityReferenceSequence(entity_references)

    def get_configurations(self) -> Tuple[EntityReference, EntityReference, EntityReference, EntityReference]:
        return (
            EntityReference(),
            EntityReference(),
            EntityReference(),
            EntityReference(),
        )


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
        with pytest.raises(ValidationError):
            LocaleConfiguration(locale, alias)

    @pytest.mark.parametrize('expected, sut, other', [
        (False, LocaleConfiguration('nl', 'NL'), 'not a locale configuration'),
        (False, LocaleConfiguration('nl', 'NL'), 999),
        (False, LocaleConfiguration('nl', 'NL'), object()),
    ])
    def test_eq(self, expected, sut, other):
        assert expected == (sut == other)


class TestLocaleConfigurationMapping(ConfigurationMappingTestBase[str, LocaleConfiguration]):
    def get_configuration_keys(self) -> Tuple[str, str, str, str]:
        return 'en', 'nl', 'uk', 'fr'

    def get_sut(self, configurations: Optional[Iterable[LocaleConfiguration]] = None) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping(configurations)

    def get_configurations(self) -> Tuple[LocaleConfiguration, LocaleConfiguration, LocaleConfiguration, LocaleConfiguration]:
        return (
            LocaleConfiguration(self.get_configuration_keys()[0]),
            LocaleConfiguration(self.get_configuration_keys()[1]),
            LocaleConfiguration(self.get_configuration_keys()[2]),
            LocaleConfiguration(self.get_configuration_keys()[3]),
        )

    def test_delitem(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[self.get_configuration_keys()[1]]
        assert [configurations[0]] == list(sut.values())

    def test_delitem_with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration('nl-NL')
        sut = LocaleConfigurationMapping([
            locale_configuration_a,
        ])
        with pytest.raises(ValidationError):
            del sut['nl-NL']

    def test_default_without_explicit_locale_configurations(self):
        sut = LocaleConfigurationMapping()
        assert LocaleConfiguration('en-US') == sut.default

    def test_default_without_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationMapping([
            locale_configuration_a,
            locale_configuration_b,
        ])
        assert locale_configuration_a == sut.default

    def test_default_with_explicit_default(self):
        locale_configuration_a = LocaleConfiguration('nl-NL')
        locale_configuration_b = LocaleConfiguration('en-US')
        sut = LocaleConfigurationMapping([
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


class ExtensionTypeConfigurationMappingTestExtension0(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension1(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension2(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension3(Extension):
    pass


class TestExtensionConfigurationMapping(ConfigurationMappingTestBase[Type[Extension], ExtensionConfiguration]):
    def get_configuration_keys(self) -> Tuple[Type[Extension], Type[Extension], Type[Extension], Type[Extension]]:
        return ExtensionTypeConfigurationMappingTestExtension0, ExtensionTypeConfigurationMappingTestExtension1, ExtensionTypeConfigurationMappingTestExtension2, ExtensionTypeConfigurationMappingTestExtension3

    def get_sut(self, configurations: Optional[Iterable[ExtensionConfiguration]] = None) -> ExtensionConfigurationMapping:
        return ExtensionConfigurationMapping(configurations)

    def get_configurations(self) -> Tuple[ExtensionConfiguration, ExtensionConfiguration, ExtensionConfiguration, ExtensionConfiguration]:
        return (
            ExtensionConfiguration(self.get_configuration_keys()[0]),
            ExtensionConfiguration(self.get_configuration_keys()[1]),
            ExtensionConfiguration(self.get_configuration_keys()[2]),
            ExtensionConfiguration(self.get_configuration_keys()[3]),
        )


class EntityTypeConfigurationTestEntityOne(UserFacingEntity, Entity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity, Entity):
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

    def test_load_with_empty_configuration(self) -> None:
        dump: Dump = {}
        with raises_error(error_type=ValidationError):
            EntityTypeConfiguration.load(dump)

    def test_load_with_minimal_configuration(self) -> None:
        dump: Dump = {
            'entity_type': get_entity_type_name(EntityTypeConfigurationTestEntityOne),
        }
        EntityTypeConfiguration.load(dump)

    @pytest.mark.parametrize('generate_html_list,', [
        True,
        False,
    ])
    def test_load_with_generate_html_list(self, generate_html_list: bool) -> None:
        dump: Dump = {
            'entity_type': get_entity_type_name(EntityTypeConfigurationTestEntityOne),
            'generate_html_list': generate_html_list,
        }
        sut = EntityTypeConfiguration.load(dump)
        assert generate_html_list == sut.generate_html_list

    def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = {
            'entity_type': 'betty.tests.test_project.EntityTypeConfigurationTestEntityOne',
        }
        assert expected == sut.dump()

    def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne, False)
        expected = {
            'entity_type': 'betty.tests.test_project.EntityTypeConfigurationTestEntityOne',
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


class EntityTypeConfigurationMappingTestEntity0(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity1(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity2(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity3(Entity):
    pass


class TestEntityTypeConfigurationMapping(ConfigurationMappingTestBase[Type[Entity], EntityTypeConfiguration]):
    def get_configuration_keys(self) -> Tuple[Type[Entity], Type[Entity], Type[Entity], Type[Entity]]:
        return EntityTypeConfigurationMappingTestEntity0, EntityTypeConfigurationMappingTestEntity1, EntityTypeConfigurationMappingTestEntity2, EntityTypeConfigurationMappingTestEntity3

    def get_sut(self, configurations: Optional[Iterable[EntityTypeConfiguration]] = None) -> EntityTypeConfigurationMapping:
        return EntityTypeConfigurationMapping(configurations)

    def get_configurations(self) -> Tuple[EntityTypeConfiguration, EntityTypeConfiguration, EntityTypeConfiguration, EntityTypeConfiguration]:
        return (
            EntityTypeConfiguration(self.get_configuration_keys()[0]),
            EntityTypeConfiguration(self.get_configuration_keys()[1]),
            EntityTypeConfiguration(self.get_configuration_keys()[2]),
            EntityTypeConfiguration(self.get_configuration_keys()[3]),
        )


class TestProjectConfiguration:
    def test_pickle(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.append(ExtensionConfiguration(Extension, True, None))
        sut.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        pickle.dumps(sut)

    def test_base_url(self):
        sut = ProjectConfiguration()
        base_url = 'https://example.com'
        sut.base_url = base_url
        assert base_url == sut.base_url

    def test_base_url_without_scheme_should_error(self):
        sut = ProjectConfiguration()
        with pytest.raises(ValidationError):
            sut.base_url = '/'

    def test_base_url_without_path_should_error(self):
        sut = ProjectConfiguration()
        with pytest.raises(ValidationError):
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
        dump: Any = ProjectConfiguration().dump()
        sut = ProjectConfiguration.load(dump)
        assert dump['base_url'] == sut.base_url
        assert 'Betty' == sut.title
        assert sut.author is None
        assert not sut.debug
        assert '' == sut.root_path
        assert not sut.clean_urls
        assert not sut.content_negotiation

    def test_load_should_load_title(self) -> None:
        title = 'My first Betty site'
        dump: Any = ProjectConfiguration().dump()
        dump['title'] = title
        sut = ProjectConfiguration.load(dump)
        assert title == sut.title

    def test_load_should_load_author(self) -> None:
        author = 'Bart'
        dump: Any = ProjectConfiguration().dump()
        dump['author'] = author
        sut = ProjectConfiguration.load(dump)
        assert author == sut.author

    def test_load_should_load_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_config: Dict = {}
        dump: Any = ProjectConfiguration().dump()
        dump['locales'] = {
            locale: locale_config,
        }
        sut = ProjectConfiguration.load(dump)
        assert LocaleConfigurationMapping([LocaleConfiguration(locale)]) == sut.locales

    def test_load_should_load_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_config = {
            'alias': alias,
        }
        dump: Any = ProjectConfiguration().dump()
        dump['locales'] = {
            locale: locale_config,
        }
        sut = ProjectConfiguration.load(dump)
        assert LocaleConfigurationMapping([LocaleConfiguration(locale, alias)]) == sut.locales

    def test_load_should_root_path(self) -> None:
        configured_root_path = '/betty/'
        expected_root_path = 'betty'
        dump: Any = ProjectConfiguration().dump()
        dump['root_path'] = configured_root_path
        sut = ProjectConfiguration.load(dump)
        assert expected_root_path == sut.root_path

    def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        dump: Any = ProjectConfiguration().dump()
        dump['clean_urls'] = clean_urls
        sut = ProjectConfiguration.load(dump)
        assert clean_urls == sut.clean_urls

    def test_load_should_content_negotiation(self) -> None:
        content_negotiation = True
        dump: Any = ProjectConfiguration().dump()
        dump['content_negotiation'] = content_negotiation
        sut = ProjectConfiguration.load(dump)
        assert content_negotiation == sut.content_negotiation

    @pytest.mark.parametrize('debug', [
        True,
        False,
    ])
    def test_load_should_load_debug(self, debug: bool) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump['debug'] = debug
        sut = ProjectConfiguration.load(dump)
        assert debug == sut.debug

    def test_load_should_load_one_extension_with_configuration(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        extension_configuration = {
            'check': False,
        }
        dump['extensions'] = {
            DummyConfigurableExtension.name(): {
                'configuration': extension_configuration,
            },
        }
        expected = ExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration())
        sut = ProjectConfiguration.load(dump)
        assert expected == sut.extensions[DummyConfigurableExtension]

    def test_load_should_load_one_extension_without_configuration(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump['extensions'] = {
            DummyNonConfigurableExtension.name(): {},
        }
        expected = ExtensionConfiguration(DummyNonConfigurableExtension, True)
        sut = ProjectConfiguration.load(dump)
        assert expected == sut.extensions[DummyNonConfigurableExtension]

    def test_load_extension_with_invalid_configuration_should_raise_error(self):
        dump: Any = ProjectConfiguration().dump()
        dump['extensions'] = {
            DummyConfigurableExtension.name(): 1337,
        }
        with raises_error(error_type=ValidationError):
            ProjectConfiguration.load(dump)

    def test_load_unknown_extension_type_name_should_error(self):
        dump: Any = ProjectConfiguration().dump()
        dump['extensions'] = {
            'non.existent.type': None,
        }
        with raises_error(error_type=ValidationError):
            ProjectConfiguration.load(dump)

    def test_load_not_an_extension_type_name_should_error(self):
        dump: Any = ProjectConfiguration().dump()
        dump['extensions'] = {
            '%s.%s' % (self.__class__.__module__, self.__class__.__name__): None,
        }
        with raises_error(error_type=ValidationError):
            ProjectConfiguration.load(dump)

    def test_load_should_error_if_invalid_config(self) -> None:
        dump: Dict = {}
        with raises_error(error_type=ValidationError):
            ProjectConfiguration.load(dump)

    def test_dump_should_dump_minimal(self) -> None:
        sut = ProjectConfiguration()
        dump: Any = sut.dump()
        assert dump['base_url'] == sut.base_url
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
        dump: Any = sut.dump()
        assert title == dump['title']

    def test_dump_should_dump_author(self) -> None:
        author = 'Bart'
        sut = ProjectConfiguration()
        sut.author = author
        dump: Any = sut.dump()
        assert author == dump['author']

    def test_dump_should_dump_locale_locale(self) -> None:
        locale = 'nl-NL'
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration()
        sut.locales.append(locale_configuration)
        sut.locales.remove('en-US')
        dump: Any = sut.dump()
        assert {
            locale: {},
        } == dump['locales']

    def test_dump_should_dump_locale_alias(self) -> None:
        locale = 'nl-NL'
        alias = 'nl'
        locale_configuration = LocaleConfiguration(locale, alias)
        sut = ProjectConfiguration()
        sut.locales.append(locale_configuration)
        sut.locales.remove('en-US')
        dump: Any = sut.dump()
        assert {
            locale: {
                'alias': alias,
            },
        } == dump['locales']

    def test_dump_should_dump_root_path(self) -> None:
        root_path = 'betty'
        sut = ProjectConfiguration()
        sut.root_path = root_path
        dump: Any = sut.dump()
        assert root_path == dump['root_path']

    def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        sut = ProjectConfiguration()
        sut.clean_urls = clean_urls
        dump: Any = sut.dump()
        assert clean_urls == dump['clean_urls']

    def test_dump_should_dump_content_negotiation(self) -> None:
        content_negotiation = True
        sut = ProjectConfiguration()
        sut.content_negotiation = content_negotiation
        dump: Any = sut.dump()
        assert content_negotiation == dump['content_negotiation']

    @pytest.mark.parametrize('debug', [
        True,
        False,
    ])
    def test_dump_should_dump_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration()
        sut.debug = debug
        dump: Any = sut.dump()
        assert debug == dump['debug']

    def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.append(ExtensionConfiguration(DummyConfigurableExtension, True, DummyConfigurableExtensionConfiguration()))
        dump: Any = sut.dump()
        expected = {
            'enabled': True,
            'configuration': {
                'check': False,
            },
        }
        assert expected == dump['extensions'][DummyConfigurableExtension.name()]

    def test_dump_should_dump_one_extension_without_configuration(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.append(ExtensionConfiguration(DummyNonConfigurableExtension))
        dump: Any = sut.dump()
        expected = {
            'enabled': True,
        }
        assert expected == dump['extensions'][DummyNonConfigurableExtension.name()]

    def test_dump_should_error_if_invalid_config(self) -> None:
        dump: Dict = {}
        with raises_error(error_type=ValidationError):
            ProjectConfiguration.load(dump)


class DummyNonConfigurableExtension(Extension):
    pass


class DummyConfigurableExtensionConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self.check = False

    def __eq__(self, other):
        return self.check == other.check

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        asserter.assert_record(Fields(
            RequiredField(
                'check',
                Assertions(asserter.assert_bool())),
        ),
        )(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return {
            'check': self.check,
        }


class DummyConfigurableExtension(ConfigurableExtension[DummyConfigurableExtensionConfiguration]):
    @classmethod
    def default_configuration(cls) -> DummyConfigurableExtensionConfiguration:
        return DummyConfigurableExtensionConfiguration()
