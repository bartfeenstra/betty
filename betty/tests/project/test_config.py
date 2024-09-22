from __future__ import annotations

from typing import Iterable, Self, Any, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, UserFacingEntity
from betty.plugin.config import PluginConfiguration
from betty.plugin.static import StaticPluginRepository
from betty.project.config import (
    EntityReference,
    EntityReferenceSequence,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    ExtensionConfiguration,
    ExtensionConfigurationMapping,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    EventTypeConfigurationMapping,
    PresenceRoleConfigurationMapping,
    PlaceTypeConfigurationMapping,
    GenderConfigurationMapping,
    CopyrightNoticeConfigurationMapping,
    CopyrightNoticeConfiguration,
)
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.model import DummyEntity
from betty.test_utils.project.extension import (
    DummyExtension,
    DummyConfigurableExtension,
    DummyConfigurableExtensionConfiguration,
)
from betty.typing import Void, Voidable

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from pytest_mock import MockerFixture
    from pathlib import Path


class _DummyNonConfigurableExtension(DummyExtension):
    pass


class EntityReferenceTestEntityOne(DummyEntity):
    pass


class EntityReferenceTestEntityTwo(DummyEntity):
    pass


class TestEntityReference:
    async def test_entity_type_with_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](
            entity_type, None, entity_type_is_constrained=True
        )
        assert sut.entity_type == entity_type
        with pytest.raises(AttributeError):
            sut.entity_type = entity_type

    async def test_entity_type_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_type is None
        sut.entity_type = entity_type
        assert sut.entity_type == entity_type

    async def test_entity_type_is_constrained(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](
            entity_type, None, entity_type_is_constrained=True
        )
        assert sut.entity_type_is_constrained

    async def test_entity_id(self) -> None:
        entity_id = "123"
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert sut.entity_id == entity_id
        del sut.entity_id
        assert sut.entity_id is None

    async def test_load_with_constraint(self) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        entity_id = "123"
        dump = entity_id
        sut.load(dump)
        assert sut.entity_id == entity_id

    @pytest.mark.parametrize(
        "dump",
        [
            {
                "entity_type": EntityReferenceTestEntityOne,
                "entity": "123",
            },
            {
                "entity_type": EntityReferenceTestEntityTwo,
                "entity": "123",
            },
            False,
            123,
        ],
    )
    async def test_load_with_constraint_without_string_should_error(
        self, dump: Dump
    ) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceTestEntityOne),
        )
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        sut.load(dump)
        assert sut.entity_type == entity_type
        assert sut.entity_id == entity_id

    async def test_load_without_constraint_without_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": None,
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_importable_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": "betty.non_existent.Entity",
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_id_should_error(
        self,
    ) -> None:
        entity_type = EntityReferenceTestEntityOne
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity": None,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_with_constraint(self) -> None:
        sut = EntityReference[Entity](Entity, None, entity_type_is_constrained=True)
        entity_id = "123"
        sut.entity_id = entity_id
        assert sut.dump() == entity_id

    async def test_dump_without_constraint(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        sut.entity_type = entity_type
        sut.entity_id = entity_id
        expected = {
            "entity_type": entity_type.plugin_id(),
            "entity": entity_id,
        }
        assert sut.dump() == expected

    async def test_update(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        entity_id = "ENTITY1"
        entity_type_is_constrained = True
        other = EntityReference[EntityReferenceTestEntityOne](
            entity_type,
            entity_id,
            entity_type_is_constrained=entity_type_is_constrained,
        )
        sut = EntityReference[EntityReferenceTestEntityOne]()
        sut.update(other)
        assert sut.entity_type == entity_type
        assert sut.entity_id == entity_id
        assert sut.entity_type_is_constrained == entity_type_is_constrained


class EntityReferenceSequenceTestEntity(DummyEntity):
    pass


class TestEntityReferenceSequence(
    ConfigurationSequenceTestBase[EntityReference[Entity]]
):
    @pytest.fixture(autouse=True)
    def _entity_types(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceSequenceTestEntity),
        )

    @override
    def get_sut(
        self, configurations: Iterable[EntityReference[Entity]] | None = None
    ) -> EntityReferenceSequence[Entity]:
        return EntityReferenceSequence(configurations)

    @override
    def get_configurations(
        self,
    ) -> tuple[
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
    ]:
        return (
            EntityReference[Entity](),
            EntityReference[Entity](EntityReferenceSequenceTestEntity),
            EntityReference[Entity](EntityReferenceSequenceTestEntity, "123"),
            EntityReference[Entity](
                EntityReferenceSequenceTestEntity,
                "123",
                entity_type_is_constrained=True,
            ),
        )

    async def test_pre_add_with_missing_required_entity_type(self) -> None:
        class DummyConstraintedEntity(DummyEntity):
            pass

        sut = EntityReferenceSequence(entity_type_constraint=DummyConstraintedEntity)
        with pytest.raises(AssertionFailed):
            sut.append(
                EntityReference(DummyEntity)  # type: ignore[arg-type]
            )

    async def test_pre_add_with_invalid_required_entity_type(self) -> None:
        class DummyConstraintedEntity(DummyEntity):
            pass

        sut = EntityReferenceSequence(entity_type_constraint=DummyConstraintedEntity)
        with pytest.raises(AssertionFailed):
            sut.append(EntityReference())

    async def test_pre_add_with_valid_value(self) -> None:
        sut = EntityReferenceSequence(entity_type_constraint=DummyEntity)
        sut.append(EntityReference(DummyEntity))


class TestLocaleConfiguration:
    async def test_locale(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.locale == locale

    async def test_alias_implicit(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.alias == locale

    async def test_alias_explicit(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        sut = LocaleConfiguration(
            locale,
            alias=alias,
        )
        assert sut.alias == alias

    async def test_invalid_alias(self) -> None:
        locale = "nl-NL"
        alias = "/"
        with pytest.raises(AssertionFailed):
            LocaleConfiguration(
                locale,
                alias=alias,
            )

    async def test_load_with_invalid_dump(self) -> None:
        dump: Dump = {}
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_with_locale(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.locale == UNDETERMINED_LOCALE

    async def test_load_with_alias(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
            "alias": "UNDETERMINED_LOCALE",
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.alias == "UNDETERMINED_LOCALE"

    async def test_dump_should_dump_minimal(self) -> None:
        sut = LocaleConfiguration("nl-NL")
        expected = {"locale": "nl-NL"}
        assert sut.dump() == expected

    async def test_dump_should_dump_alias(self) -> None:
        sut = LocaleConfiguration("nl-NL", alias="nl")
        expected = {"locale": "nl-NL", "alias": "nl"}
        assert sut.dump() == expected

    async def test_update(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        other = LocaleConfiguration(locale, alias=alias)
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.update(other)
        assert sut.locale == locale
        assert sut.alias == alias


class TestLocaleConfigurationMapping(
    ConfigurationMappingTestBase[str, LocaleConfiguration]
):
    @override
    def get_sut(
        self, configurations: Iterable[Configuration] | None = None
    ) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping(configurations)  # type: ignore[arg-type]

    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return ("en", "nl", "uk", "fr")

    @override
    def get_configurations(
        self,
    ) -> tuple[
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
    ]:
        return (
            LocaleConfiguration("en"),
            LocaleConfiguration("nl"),
            LocaleConfiguration("uk"),
            LocaleConfiguration("fr"),
        )

    async def test_update(self) -> None:
        sut = LocaleConfigurationMapping()
        configurations = self.get_configurations()
        other = LocaleConfigurationMapping(configurations)
        sut.update(other)
        assert list(sut) == list(other)

    async def test___delitem__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0]])
        del sut[configurations[0].locale]
        with pytest.raises(KeyError):
            sut[configurations[0].locale]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    async def test___delitem___with_locale(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        del sut[configurations[0].locale]
        with pytest.raises(KeyError):
            sut[configurations[0].locale]

    async def test___delitem___with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
            ]
        )
        del sut["nl-NL"]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    async def test_default_without_explicit_locale_configurations(self) -> None:
        sut = LocaleConfigurationMapping()
        assert sut.default.locale == DEFAULT_LOCALE

    async def test_default_without_explicit_default(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        locale_configuration_b = LocaleConfiguration("en-US")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
                locale_configuration_b,
            ]
        )
        assert sut.default == locale_configuration_a

    @override
    async def test_replace_without_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        self.get_configurations()
        sut.replace()
        assert len(sut) == 1

    @override
    async def test_replace_with_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        configurations = self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)

    def test_multilingual_with_one_configuration(self) -> None:
        sut = self.get_sut()
        assert not sut.multilingual

    def test_multilingual_with_multiple_configurations(self) -> None:
        sut = self.get_sut()
        sut.replace(*self.get_configurations())
        assert sut.multilingual


class _DummyConfiguration(Configuration):
    @override
    def update(self, other: Self) -> None:
        pass  # pragma: no cover

    @override
    def load(self, dump: Dump) -> None:
        pass  # pragma: no cover

    @override
    def dump(self) -> Voidable[Dump]:
        return Void


class TestExtensionConfiguration:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(DummyExtension, DummyConfigurableExtension),
        )

    async def test_extension_type(self) -> None:
        extension_type = DummyExtension
        sut = ExtensionConfiguration(extension_type)
        assert sut.extension_type == extension_type

    async def test_enabled(self) -> None:
        enabled = True
        sut = ExtensionConfiguration(
            DummyExtension,
            enabled=enabled,
        )
        assert sut.enabled == enabled
        sut.enabled = False

    async def test_extension_configuration(self) -> None:
        extension_type_configuration = _DummyConfiguration()
        sut = ExtensionConfiguration(
            DummyConfigurableExtension,
            extension_configuration=extension_type_configuration,
        )
        assert sut.extension_configuration == extension_type_configuration

    async def test_load_without_extension(self) -> None:
        with raises_error(error_type=AssertionFailed):
            ExtensionConfiguration(DummyExtension).load({})

    async def test_load_with_extension(self) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        sut.load({"extension": DummyConfigurableExtension.plugin_id()})
        assert sut.extension_type == DummyConfigurableExtension
        assert sut.enabled

    async def test_load_with_enabled(self) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        sut.load(
            {"extension": DummyConfigurableExtension.plugin_id(), "enabled": False}
        )
        assert not sut.enabled

    async def test_load_with_configuration(self) -> None:
        sut = ExtensionConfiguration(DummyConfigurableExtension)
        sut.load(
            {
                "extension": DummyConfigurableExtension.plugin_id(),
                "configuration": {
                    "check": True,
                },
            }
        )
        extension_configuration = sut.extension_configuration
        assert isinstance(
            extension_configuration, DummyConfigurableExtensionConfiguration
        )
        assert extension_configuration.check

    async def test_load_with_configuration_for_non_configurable_extension_should_error(
        self,
    ) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        with pytest.raises(AssertionFailed):
            sut.load(
                {
                    "extension": DummyExtension.plugin_id(),
                    "configuration": {
                        "check": True,
                    },
                }
            )

    async def test_dump_should_dump_minimal(self) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        expected = {
            "extension": DummyExtension.plugin_id(),
            "enabled": True,
        }
        assert sut.dump() == expected

    async def test_dump_should_dump_extension_configuration(self) -> None:
        sut = ExtensionConfiguration(DummyConfigurableExtension)
        expected = {
            "extension": DummyConfigurableExtension.plugin_id(),
            "enabled": True,
            "configuration": {
                "check": False,
            },
        }
        assert sut.dump() == expected

    async def test_update_should_update_minimal(self) -> None:
        class _OtherDummyExtension(DummyExtension):
            pass

        other = ExtensionConfiguration(_OtherDummyExtension)
        sut = ExtensionConfiguration(DummyExtension)
        sut.update(other)
        assert sut.extension_type is _OtherDummyExtension
        assert sut.enabled
        assert sut.extension_configuration is None

    async def test_update_should_update_extension_configuration(self) -> None:
        other = ExtensionConfiguration(DummyConfigurableExtension)
        sut = ExtensionConfiguration(DummyExtension)
        sut.update(other)
        assert isinstance(
            sut.extension_configuration, DummyConfigurableExtensionConfiguration
        )


class ExtensionTypeConfigurationMappingTestExtension0(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension1(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension2(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension3(DummyExtension):
    pass


class TestExtensionConfigurationMapping(
    ConfigurationMappingTestBase[type[Extension], ExtensionConfiguration]
):
    def get_configuration_keys(
        self,
    ) -> tuple[type[Extension], type[Extension], type[Extension], type[Extension]]:
        return (
            ExtensionTypeConfigurationMappingTestExtension0,
            ExtensionTypeConfigurationMappingTestExtension1,
            ExtensionTypeConfigurationMappingTestExtension2,
            ExtensionTypeConfigurationMappingTestExtension3,
        )

    def get_sut(
        self, configurations: Iterable[ExtensionConfiguration] | None = None
    ) -> ExtensionConfigurationMapping:
        return ExtensionConfigurationMapping(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        ExtensionConfiguration,
        ExtensionConfiguration,
        ExtensionConfiguration,
        ExtensionConfiguration,
    ]:
        return (
            ExtensionConfiguration(self.get_configuration_keys()[0]),
            ExtensionConfiguration(self.get_configuration_keys()[1]),
            ExtensionConfiguration(self.get_configuration_keys()[2], enabled=False),
            ExtensionConfiguration(self.get_configuration_keys()[3], enabled=False),
        )

    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(*self.get_configuration_keys()),
        )

    async def test_enable(self) -> None:
        sut = ExtensionConfigurationMapping()
        sut.enable(DummyExtension)
        assert sut[DummyExtension].enabled

    async def test_update(self) -> None:
        other = ExtensionConfigurationMapping()
        other.enable(DummyExtension)
        sut = ExtensionConfigurationMapping()
        sut.update(other)
        assert sut[DummyExtension].enabled


class EntityTypeConfigurationTestEntityOne(UserFacingEntity, DummyEntity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity, DummyEntity):
    pass


class TestEntityTypeConfiguration:
    async def test_entity_type(self) -> None:
        entity_type = EntityTypeConfigurationTestEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert sut.entity_type == entity_type

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.generate_html_list = generate_html_list
        assert sut.generate_html_list == generate_html_list

    async def test_generate_html_list_for_non_user_facing_entity_should_error(
        self,
    ) -> None:
        sut = EntityTypeConfiguration(DummyEntity)
        with pytest.raises(AssertionFailed):
            sut.generate_html_list = True

    async def test_load_with_empty_configuration(self) -> None:
        dump: Dump = {}
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_with_minimal_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityTypeConfigurationTestEntityOne),
        )
        dump: Dump = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_load_with_generate_html_list(
        self, generate_html_list: bool, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityTypeConfigurationTestEntityOne),
        )
        dump: Dump = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)
        assert sut.generate_html_list == generate_html_list

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
        }
        assert sut.dump() == expected

    async def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(
            entity_type=EntityTypeConfigurationTestEntityOne,
            generate_html_list=False,
        )
        expected = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_update(self) -> None:
        other = EntityTypeConfiguration(
            entity_type=EntityTypeConfigurationTestEntityOne,
            generate_html_list=True,
        )
        sut = EntityTypeConfiguration(
            entity_type=EntityTypeConfigurationTestEntityOther
        )
        sut.update(other)
        assert sut.entity_type is EntityTypeConfigurationTestEntityOne
        assert sut.generate_html_list


class EntityTypeConfigurationMappingTestEntity0(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity1(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity2(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity3(DummyEntity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[type[Entity], EntityTypeConfiguration]
):
    @pytest.fixture(autouse=True)
    def _entity_types(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(
                EntityTypeConfigurationMappingTestEntity0,
                EntityTypeConfigurationMappingTestEntity1,
                EntityTypeConfigurationMappingTestEntity2,
                EntityTypeConfigurationMappingTestEntity3,
            ),
        )

    def get_configuration_keys(
        self,
    ) -> tuple[type[Entity], type[Entity], type[Entity], type[Entity]]:
        return (
            EntityTypeConfigurationMappingTestEntity0,
            EntityTypeConfigurationMappingTestEntity1,
            EntityTypeConfigurationMappingTestEntity2,
            EntityTypeConfigurationMappingTestEntity3,
        )

    def get_sut(
        self, configurations: Iterable[EntityTypeConfiguration] | None = None
    ) -> EntityTypeConfigurationMapping:
        return EntityTypeConfigurationMapping(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        EntityTypeConfiguration,
        EntityTypeConfiguration,
        EntityTypeConfiguration,
        EntityTypeConfiguration,
    ]:
        return (
            EntityTypeConfiguration(self.get_configuration_keys()[0]),
            EntityTypeConfiguration(self.get_configuration_keys()[1]),
            EntityTypeConfiguration(self.get_configuration_keys()[2]),
            EntityTypeConfiguration(self.get_configuration_keys()[3]),
        )


class TestCopyrightNoticeConfiguration:
    def test___init___with_summary(self) -> None:
        summary = "My First Copyright Summary"
        sut = CopyrightNoticeConfiguration("-", "", summary=summary, text="")
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test___init___with_text(self) -> None:
        text = "My First Copyright Text"
        sut = CopyrightNoticeConfiguration("-", "", summary="", text=text)
        assert sut.text[UNDETERMINED_LOCALE] == text

    def test_summary(self) -> None:
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        summary = "My First Copyright Summary"
        sut.summary = summary
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test_text(self) -> None:
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        text = "My First Copyright Text"
        sut.text = text
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_update(self) -> None:
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        summary = "My First Copyright Summary"
        text = "My First Copyright Text"
        other = CopyrightNoticeConfiguration(
            "-", "", description="", summary=summary, text=text
        )
        sut.update(other)
        assert sut.summary[UNDETERMINED_LOCALE] == "My First Copyright Summary"
        assert sut.text[UNDETERMINED_LOCALE] == "My First Copyright Text"

    async def test_load(self) -> None:
        summary = "My First Copyright Summary"
        text = "My First Copyright Text"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": summary,
            "text": text,
        }
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        sut.load(dump)
        assert sut.summary[UNDETERMINED_LOCALE] == summary
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load_with_missing_summary(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "text": "",
        }
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_load_with_missing_text(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": "",
        }
        sut = CopyrightNoticeConfiguration("-", "", summary="", text="")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_dump(self) -> None:
        summary = "My First Copyright Summary"
        text = "My First Copyright Text"
        sut = CopyrightNoticeConfiguration("-", "", summary=summary, text=text)
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text


class TestCopyrightNoticeConfigurationMapping(
    ConfigurationMappingTestBase[str, CopyrightNoticeConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        CopyrightNoticeConfiguration,
        CopyrightNoticeConfiguration,
        CopyrightNoticeConfiguration,
        CopyrightNoticeConfiguration,
    ]:
        return (
            CopyrightNoticeConfiguration("foo", "Foo", summary="", text=""),
            CopyrightNoticeConfiguration("bar", "Bar", summary="", text=""),
            CopyrightNoticeConfiguration("baz", "Baz", summary="", text=""),
            CopyrightNoticeConfiguration("qux", "Qux", summary="", text=""),
        )

    @override
    def get_sut(
        self, configurations: Iterable[CopyrightNoticeConfiguration] | None = None
    ) -> CopyrightNoticeConfigurationMapping:
        return CopyrightNoticeConfigurationMapping(configurations)


class TestEventTypeConfigurationMapping(
    ConfigurationMappingTestBase[str, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
    ]:
        return (
            PluginConfiguration("foo", "Foo"),
            PluginConfiguration("bar", "Bar"),
            PluginConfiguration("baz", "Baz"),
            PluginConfiguration("qux", "Qux"),
        )

    @override
    def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> EventTypeConfigurationMapping:
        return EventTypeConfigurationMapping(configurations)


class TestPlaceTypeConfigurationMapping(
    ConfigurationMappingTestBase[str, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
    ]:
        return (
            PluginConfiguration("foo", "Foo"),
            PluginConfiguration("bar", "Bar"),
            PluginConfiguration("baz", "Baz"),
            PluginConfiguration("qux", "Qux"),
        )

    @override
    def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> PlaceTypeConfigurationMapping:
        return PlaceTypeConfigurationMapping(configurations)


class TestPresenceRoleConfigurationMapping(
    ConfigurationMappingTestBase[str, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
    ]:
        return (
            PluginConfiguration("foo", "Foo"),
            PluginConfiguration("bar", "Bar"),
            PluginConfiguration("baz", "Baz"),
            PluginConfiguration("qux", "Qux"),
        )

    @override
    def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> PresenceRoleConfigurationMapping:
        return PresenceRoleConfigurationMapping(configurations)


class TestGenderConfigurationMapping(
    ConfigurationMappingTestBase[str, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
    ]:
        return (
            PluginConfiguration("foo", "Foo"),
            PluginConfiguration("bar", "Bar"),
            PluginConfiguration("baz", "Baz"),
            PluginConfiguration("qux", "Qux"),
        )

    @override
    def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> GenderConfigurationMapping:
        return GenderConfigurationMapping(configurations)


class TestProjectConfiguration:
    async def test_configuration_file_path(self, tmp_path: Path) -> None:
        old_configuration_file_path = tmp_path / "betty.json"
        sut = ProjectConfiguration(old_configuration_file_path)
        assert sut.configuration_file_path == old_configuration_file_path
        new_configuration_file_path = tmp_path / "betty.yaml"
        sut.configuration_file_path = new_configuration_file_path
        assert sut.configuration_file_path == new_configuration_file_path
        # Assert that setting the path to its existing value is a no-op.
        sut.configuration_file_path = new_configuration_file_path
        assert sut.configuration_file_path == new_configuration_file_path

    async def test_project_directory_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.project_directory_path == tmp_path

    async def test_output_directory_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert tmp_path in sut.output_directory_path.parents

    async def test_assets_directory_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert tmp_path in sut.assets_directory_path.parents

    async def test_www_directory_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert tmp_path in sut.www_directory_path.parents

    async def test_localize_www_directory_path_monolingual(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE not in str(actual)

    async def test_localize_www_directory_path_multilingual(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.append(LocaleConfiguration("nl-NL"))
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE in str(actual)

    async def test_lifetime_threshold(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    async def test_locales(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert DEFAULT_LOCALE in sut.locales

    async def test_extensions(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert len(sut.extensions) == 0

    async def test_entity_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert len(sut.entity_types)

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.debug = debug
        assert sut.debug == debug

    async def test_title(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        title = "My First Betty Site"
        sut.title = title
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_name(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        name = "my-first-betty-site"
        sut.name = name
        assert sut.name == name

    async def test_url(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    async def test_url_without_scheme_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(AssertionFailed):
            sut.url = "/"

    async def test_url_without_path_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(AssertionFailed):
            sut.url = "file://"

    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            ("https://example.com", "https://example.com"),
            ("https://example.com", "https://example.com/"),
            ("https://example.com", "https://example.com/root-path"),
        ],
    )
    async def test_base_url(self, expected: str, tmp_path: Path, url: str) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.url = url
        assert sut.base_url == expected

    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            ("", "https://example.com"),
            ("", "https://example.com/"),
            ("/root-path", "https://example.com/root-path"),
            ("/root-path", "https://example.com/root-path/"),
        ],
    )
    async def test_root_path(self, expected: str, tmp_path: Path, url: str) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.url = url
        assert sut.root_path == expected

    async def test_clean_urls(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert sut.clean_urls == clean_urls

    async def test_author_without_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert not sut.author

    async def test_author_with_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        author = "Bart"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test___init___with_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = ProjectConfiguration(tmp_path / "betty.json", logo=logo)
        assert sut.logo == logo

    async def test_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.logo = logo
        assert sut.logo == logo

    async def test_copyright_notices(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.copyright_notices is sut.copyright_notices

    async def test_event_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.event_types is sut.event_types

    async def test_place_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.place_types is sut.place_types

    async def test_presence_roles(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.presence_roles is sut.presence_roles

    async def test_genders(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.genders is sut.genders

    async def test_load_should_load_minimal(self, tmp_path: Path) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert not sut.clean_urls

    async def test_load_should_load_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["name"] = name
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.name == name

    async def test_load_should_load_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["title"] = title
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_load_should_load_author(self, tmp_path: Path) -> None:
        author = "Bart"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["author"] = author
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load_should_load_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["logo"] = str(logo)
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.logo == logo

    async def test_load_should_load_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        dump = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["locales"] = [{"locale": locale}]
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales

    async def test_load_should_load_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["locales"] = [{"locale": locale, "alias": alias}]
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales
        actual = sut.locales[locale]
        assert actual.alias == alias

    async def test_load_should_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["clean_urls"] = clean_urls
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.clean_urls == clean_urls

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_load_should_load_debug(self, debug: bool, tmp_path: Path) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["debug"] = debug
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.debug == debug

    async def test_load_should_load_one_extension_with_configuration(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(DummyConfigurableExtension),
        )
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        extension_configuration = {
            "check": False,
        }
        dump["extensions"] = {
            DummyConfigurableExtension.plugin_id(): {
                "configuration": extension_configuration,
            },
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        actual = sut.extensions[DummyConfigurableExtension]
        assert actual.enabled
        assert isinstance(
            actual.extension_configuration, DummyConfigurableExtensionConfiguration
        )

    async def test_load_should_load_one_extension_without_configuration(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(_DummyNonConfigurableExtension),
        )
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            _DummyNonConfigurableExtension.plugin_id(): {},
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        actual = sut.extensions[_DummyNonConfigurableExtension]
        assert actual.enabled
        assert actual.extension_configuration is None

    async def test_load_extension_with_invalid_configuration_should_raise_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            DummyConfigurableExtension.plugin_id(): 1337,
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_unknown_extension_type_name_should_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            "non.existent.type": {},
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_not_an_extension_type_name_should_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            f"{self.__class__.__module__}.{self.__class__.__name__}": {}
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    @pytest.mark.parametrize(
        "event_types_configuration",
        [
            {},
            {"foo": {"label": "Foo"}},
        ],
    )
    async def test_load_should_load_event_types(
        self, event_types_configuration: DumpMapping[Dump], tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["event_types"] = event_types_configuration
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        if event_types_configuration:
            assert sut.dump()["event_types"] == event_types_configuration

    @pytest.mark.parametrize(
        "place_types_configuration",
        [
            {},
            {"foo": {"label": "Foo"}},
        ],
    )
    async def test_load_should_load_place_types(
        self, place_types_configuration: DumpMapping[Dump], tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["place_types"] = place_types_configuration
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        if place_types_configuration:
            assert sut.dump()["place_types"] == place_types_configuration

    @pytest.mark.parametrize(
        "presence_roles_configuration",
        [
            {},
            {"foo": {"label": "Foo"}},
        ],
    )
    async def test_load_should_load_presence_roles(
        self, presence_roles_configuration: DumpMapping[Dump], tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["presence_roles"] = presence_roles_configuration
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        if presence_roles_configuration:
            assert sut.dump()["presence_roles"] == presence_roles_configuration

    @pytest.mark.parametrize(
        "genders_configuration",
        [
            {},
            {"foo": {"label": "Foo"}},
        ],
    )
    async def test_load_should_load_genders(
        self, genders_configuration: DumpMapping[Dump], tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["genders"] = genders_configuration
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        if genders_configuration:
            assert sut.dump()["genders"] == genders_configuration

    async def test_load_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_should_dump_minimal(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump: Any = sut.dump()
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_dump_should_dump_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.title = title
        dump: Any = sut.dump()
        assert title == dump["title"]

    async def test_dump_should_dump_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.name = name
        dump: Any = sut.dump()
        assert dump["name"] == name

    async def test_dump_should_dump_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.author = author
        dump: Any = sut.dump()
        assert author == dump["author"]

    async def test_dump_should_dumpo_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.logo = logo
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["logo"] == str(logo)

    async def test_dump_should_dump_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump: Any = sut.dump()
        assert dump["locales"] == [
            {"locale": locale},
        ]

    async def test_dump_should_dump_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump: Any = sut.dump()
        assert dump["locales"] == [
            {"locale": locale, "alias": alias},
        ]

    async def test_dump_should_dump_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.clean_urls = clean_urls
        dump: Any = sut.dump()
        assert clean_urls == dump["clean_urls"]

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_dump_should_dump_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.debug = debug
        dump: Any = sut.dump()
        assert debug == dump["debug"]

    async def test_dump_should_dump_one_extension_with_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.extensions.append(
            ExtensionConfiguration(
                DummyConfigurableExtension,
                extension_configuration=DummyConfigurableExtensionConfiguration(),
            )
        )
        dump: Any = sut.dump()
        expected = {
            "enabled": True,
            "configuration": {
                "check": False,
            },
        }
        assert expected == dump["extensions"][DummyConfigurableExtension.plugin_id()]

    async def test_dump_should_dump_one_extension_without_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.extensions.enable(_DummyNonConfigurableExtension)
        dump: Any = sut.dump()
        expected = {
            "enabled": True,
        }
        assert (
            expected == dump["extensions"][_DummyNonConfigurableExtension.plugin_id()]
        )

    async def test_dump_should_dump_event_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.event_types.append(PluginConfiguration("foo", "Foo"))
        dump: Any = sut.dump()
        expected = {"foo": {"label": "Foo"}}
        assert expected == dump["event_types"]

    async def test_dump_should_dump_place_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.place_types.append(PluginConfiguration("foo", "Foo"))
        dump: Any = sut.dump()
        expected = {"foo": {"label": "Foo"}}
        assert expected == dump["place_types"]

    async def test_dump_should_dump_presence_roles(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.presence_roles.append(PluginConfiguration("foo", "Foo"))
        dump: Any = sut.dump()
        expected = {"foo": {"label": "Foo"}}
        assert expected == dump["presence_roles"]

    async def test_dump_should_dump_genders(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.genders.append(PluginConfiguration("foo", "Foo"))
        dump: Any = sut.dump()
        expected = {"foo": {"label": "Foo"}}
        assert expected == dump["genders"]

    async def test_dump_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_update(self, tmp_path: Path) -> None:
        url = "https://betty.example.com"
        name = "my-first-betty-site"
        title = "My First Betty Site"
        author = "Bart Feenstra"
        clean_urls = True
        debug = True
        lifetime_threshold = 99
        locales = [LocaleConfiguration("nl-NL")]
        extensions = [ExtensionConfiguration(DummyExtension)]
        entity_types = [EntityTypeConfiguration(DummyEntity)]
        other = ProjectConfiguration(
            tmp_path / "other" / "betty.json",
            url=url,
            name=name,
            title=title,
            author=author,
            clean_urls=clean_urls,
            debug=debug,
            lifetime_threshold=lifetime_threshold,
            locales=locales,
            extensions=extensions,
            entity_types=entity_types,
            event_types=[
                PluginConfiguration("my-first-event-type", "My First Event Type")
            ],
            place_types=[
                PluginConfiguration("my-first-place-type", "My First Place Type")
            ],
            presence_roles=[
                PluginConfiguration("my-first-presence-role", "My First Presence Role")
            ],
            genders=[PluginConfiguration("my-first-gender", "My First Gender")],
        )
        sut = ProjectConfiguration(tmp_path / "sut" / "betty.json")
        sut.update(other)
        assert sut.url == url
        assert sut.title.localize(DEFAULT_LOCALIZER) == title
        assert sut.author.localize(DEFAULT_LOCALIZER) == author
        assert sut.clean_urls == clean_urls
        assert sut.debug == debug
        assert sut.lifetime_threshold == lifetime_threshold
        assert list(sut.locales.values()) == locales
        assert list(sut.extensions.values()) == extensions
        assert list(sut.entity_types.values()) == entity_types
        assert (
            sut.event_types["my-first-event-type"].label.localize(DEFAULT_LOCALIZER)
            == "My First Event Type"
        )
        assert (
            sut.genders["my-first-gender"].label.localize(DEFAULT_LOCALIZER)
            == "My First Gender"
        )
        assert (
            sut.place_types["my-first-place-type"].label.localize(DEFAULT_LOCALIZER)
            == "My First Place Type"
        )
        assert (
            sut.presence_roles["my-first-presence-role"].label.localize(
                DEFAULT_LOCALIZER
            )
            == "My First Presence Role"
        )
