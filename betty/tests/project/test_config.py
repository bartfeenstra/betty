from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.gender import GenderDefinition
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.copyright_notice.copyright_notices import ProjectAuthor
from betty.exception import HumanFacingException
from betty.license import LicenseDefinition
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import CountablePlain, Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.model import Entity, EntityDefinition
from betty.plugin.config import PluginInstanceConfiguration
from betty.plugin.static import StaticPluginRepository
from betty.project.config import (
    CopyrightNoticeDefinitionConfiguration,
    CopyrightNoticeDefinitionConfigurationMapping,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    EventTypeDefinitionConfiguration,
    EventTypeDefinitionConfigurationMapping,
    ExtensionInstanceConfigurationMapping,
    GenderDefinitionConfiguration,
    GenderDefinitionConfigurationMapping,
    LicenseDefinitionConfiguration,
    LicenseDefinitionConfigurationMapping,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    PlaceTypeDefinitionConfiguration,
    PlaceTypeDefinitionConfigurationMapping,
    PresenceRoleDefinitionConfiguration,
    PresenceRoleDefinitionConfigurationMapping,
    ProjectConfiguration,
)
from betty.project.extension import Extension, ExtensionDefinition
from betty.serde.format import FormatError
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.exception import raises_error
from betty.test_utils.model import DummyEntityOne, DummyNonPublicFacingEntityOne
from betty.test_utils.plugin.config import PluginDefinitionConfigurationMappingTestBase
from betty.test_utils.project.extension import (
    DummyConfigurableExtension,
    DummyExtension,
)
from betty.typing import Void

if TYPE_CHECKING:
    from pathlib import Path

    from betty.serde.dump import Dump, DumpMapping
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurationKeys,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


@ExtensionDefinition(
    id="dummy-non-configurable",
    label=Plain(""),
)
class _DummyNonConfigurableExtension(Extension):
    pass


class TestLocaleConfiguration:
    async def test_locale(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.locale == locale

    async def test_alias__implicit(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.alias == locale

    async def test_alias__explicit(self) -> None:
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
        with pytest.raises(HumanFacingException):
            LocaleConfiguration(
                locale,
                alias=alias,
            )

    async def test_load__with_invalid_dump(self) -> None:
        dump: Dump = {}
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_load__with_locale(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.locale == UNDETERMINED_LOCALE

    async def test_load__with_alias(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
            "alias": "UNDETERMINED_LOCALE",
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.alias == "UNDETERMINED_LOCALE"

    async def test_dump__should_dump_minimal(self) -> None:
        sut = LocaleConfiguration("nl-NL")
        expected = {"locale": "nl-NL", "alias": None}
        assert sut.dump() == expected

    async def test_dump__should_dump_alias(self) -> None:
        sut = LocaleConfiguration("nl-NL", alias="nl")
        expected = {"locale": "nl-NL", "alias": "nl"}
        assert sut.dump() == expected


class TestLocaleConfigurationMapping(
    ConfigurationMappingTestBase[str, LocaleConfiguration]
):
    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[LocaleConfiguration, MachineName]:
        return LocaleConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[str]:
        return ("en", "nl", "uk", "fr")

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[LocaleConfiguration]:
        return (
            LocaleConfiguration("en"),
            LocaleConfiguration("nl"),
            LocaleConfiguration("uk"),
            LocaleConfiguration("fr"),
        )

    @override
    def test___delitem__(  # type: ignore[override]
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[LocaleConfiguration, str],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut = new_sut([sut_configurations[0]])
        del sut[sut_configurations[0].locale]
        with pytest.raises(KeyError):
            sut[sut_configurations[0].locale]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    def test___delitem____with_locale(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[LocaleConfiguration, str],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut = new_sut([sut_configurations[0], sut_configurations[1]])
        del sut[sut_configurations[0].locale]
        with pytest.raises(KeyError):
            sut[sut_configurations[0].locale]

    def test___delitem____with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
            ]
        )
        del sut["nl-NL"]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    def test_default__without_explicit_locale_configurations(self) -> None:
        sut = LocaleConfigurationMapping()
        assert sut.default.locale == DEFAULT_LOCALE

    def test_default__without_explicit_default(self) -> None:
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
    def test_replace__without_items(  # type: ignore[override]
        self,
        sut: LocaleConfigurationMapping,
    ) -> None:
        sut.clear()
        assert len(sut) == 1
        sut.replace()
        assert len(sut) == 1

    @override
    def test_replace__with_items(  # type: ignore[override]
        self,
        sut: LocaleConfigurationMapping,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut.clear()
        assert len(sut) == 1
        sut.replace(*sut_configurations)
        assert len(sut) == len(sut_configurations)

    def test_multilingual__with_one_configuration(
        self, sut: LocaleConfigurationMapping
    ) -> None:
        assert not sut.multilingual

    def test_multilingual__with_multiple_configurations(
        self,
        sut: LocaleConfigurationMapping,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        assert sut.multilingual


@ExtensionDefinition(
    id="extension-instance-configuration-mapping-test-extension-0",
    label=Plain(""),
)
class ExtensionInstanceConfigurationMappingTestExtension0(Extension):
    pass


@ExtensionDefinition(
    id="extension-instance-configuration-mapping-test-extension-1",
    label=Plain(""),
)
class ExtensionInstanceConfigurationMappingTestExtension1(Extension):
    pass


@ExtensionDefinition(
    id="extension-instance-configuration-mapping-test-extension-2",
    label=Plain(""),
)
class ExtensionInstanceConfigurationMappingTestExtension2(Extension):
    pass


@ExtensionDefinition(
    id="extension-instance-configuration-mapping-test-extension-3",
    label=Plain(""),
)
class ExtensionInstanceConfigurationMappingTestExtension3(Extension):
    pass


class TestExtensionInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        MachineName, PluginInstanceConfiguration[ExtensionDefinition, Extension]
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            ExtensionInstanceConfigurationMappingTestExtension0.plugin.id,
            ExtensionInstanceConfigurationMappingTestExtension1.plugin.id,
            ExtensionInstanceConfigurationMappingTestExtension2.plugin.id,
            ExtensionInstanceConfigurationMappingTestExtension3.plugin.id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[ExtensionDefinition, Extension], MachineName
    ]:
        return ExtensionInstanceConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            MachineName
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginInstanceConfiguration[ExtensionDefinition, Extension]
    ]:
        return (
            PluginInstanceConfiguration(sut_configuration_keys[0]),
            PluginInstanceConfiguration(sut_configuration_keys[1]),
            PluginInstanceConfiguration(sut_configuration_keys[2]),
            PluginInstanceConfiguration(sut_configuration_keys[3]),
        )

    def test_enable(self) -> None:
        sut = ExtensionInstanceConfigurationMapping()
        sut.enable(DummyExtension)
        assert DummyExtension.plugin in sut


class TestEntityTypeConfiguration:
    async def test_id__with___init___entity_type(self) -> None:
        entity_type = DummyEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert sut.id == entity_type.plugin.id

    async def test_id__with___init___entity_type_id(self) -> None:
        entity_type_id = DummyEntityOne.plugin.id
        sut = EntityTypeConfiguration(entity_type_id)
        assert sut.id == entity_type_id

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne)
        sut.generate_html_list = generate_html_list
        assert sut.generate_html_list == generate_html_list

    async def test_load__with_empty_configuration(self) -> None:
        dump: Dump = {}
        sut = EntityTypeConfiguration(DummyEntityOne)
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    def test_load__with_minimal_configuration(self) -> None:
        dump: Dump = {
            "id": DummyEntityOne.plugin.id,
        }
        sut = EntityTypeConfiguration(DummyEntityOne)
        sut.load(dump)

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    def test_load__with_generate_html_list(self, generate_html_list: bool) -> None:
        dump: Dump = {
            "id": DummyEntityOne.plugin.id,
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration(DummyEntityOne)
        sut.load(dump)
        assert sut.generate_html_list == generate_html_list

    async def test_dump__with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne)
        expected = {
            "id": DummyEntityOne.plugin.id,
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_dump__with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne, generate_html_list=False)
        expected = {
            "id": DummyEntityOne.plugin.id,
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_validate__with_generate_html_list_with_non_public_facing_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityTypeConfiguration(
            DummyNonPublicFacingEntityOne, generate_html_list=True
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(
                StaticPluginRepository(
                    EntityDefinition, DummyNonPublicFacingEntityOne.plugin
                )
            )


@EntityDefinition(
    id="zero",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class EntityTypeConfigurationMappingTestEntity0(Entity):
    pass


@EntityDefinition(
    id="one",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class EntityTypeConfigurationMappingTestEntity1(Entity):
    pass


@EntityDefinition(
    id="two",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class EntityTypeConfigurationMappingTestEntity2(Entity):
    pass


@EntityDefinition(
    id="three",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class EntityTypeConfigurationMappingTestEntity3(Entity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[MachineName, EntityTypeConfiguration]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            EntityTypeConfigurationMappingTestEntity0.plugin.id,
            EntityTypeConfigurationMappingTestEntity1.plugin.id,
            EntityTypeConfigurationMappingTestEntity2.plugin.id,
            EntityTypeConfigurationMappingTestEntity3.plugin.id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[EntityTypeConfiguration, MachineName]:
        return EntityTypeConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            MachineName
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[EntityTypeConfiguration]:
        return (
            EntityTypeConfiguration(sut_configuration_keys[0]),
            EntityTypeConfiguration(sut_configuration_keys[1]),
            EntityTypeConfiguration(sut_configuration_keys[2]),
            EntityTypeConfiguration(sut_configuration_keys[3]),
        )

    async def test_validate__with_item_error_should_error(self) -> None:
        sut = EntityTypeConfigurationMapping(
            [
                EntityTypeConfiguration(
                    DummyNonPublicFacingEntityOne, generate_html_list=True
                )
            ]
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(
                StaticPluginRepository(
                    EntityDefinition, DummyNonPublicFacingEntityOne.plugin
                )
            )


class TestCopyrightNoticeConfiguration:
    def test___init____with_summary(self) -> None:
        summary = "My First Copyright Summary"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary=summary, text=""
        )
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test___init____with_text(self) -> None:
        text = "My First Copyright Text"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=text
        )
        assert sut.text[UNDETERMINED_LOCALE] == text

    def test_summary(self) -> None:
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        summary = "My First Copyright Summary"
        sut.summary = summary
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test_text(self) -> None:
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        text = "My First Copyright Text"
        sut.text = text
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load(self) -> None:
        summary = "My First Copyright Summary"
        text = "My First Copyright Text"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": summary,
            "text": text,
        }
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        sut.load(dump)
        assert sut.summary[UNDETERMINED_LOCALE] == summary
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load__with_missing_summary(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "text": "",
        }
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        with pytest.raises(HumanFacingException):
            sut.load(dump)

    async def test_load__with_missing_text(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": "",
        }
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        with pytest.raises(HumanFacingException):
            sut.load(dump)

    async def test_dump(self) -> None:
        summary = "My First Copyright Summary"
        text = "My First Copyright Text"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary=summary, text=text
        )
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text


class TestCopyrightNoticeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        CopyrightNoticeDefinition, CopyrightNoticeDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        CopyrightNoticeDefinitionConfiguration
    ]:
        return (
            CopyrightNoticeDefinitionConfiguration(
                id="foo", label="Foo", summary="", text=""
            ),
            CopyrightNoticeDefinitionConfiguration(
                id="bar", label="Bar", summary="", text=""
            ),
            CopyrightNoticeDefinitionConfiguration(
                id="baz", label="Baz", summary="", text=""
            ),
            CopyrightNoticeDefinitionConfiguration(
                id="qux", label="Qux", summary="", text=""
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        CopyrightNoticeDefinitionConfigurationMapping, MachineName
    ]:
        return CopyrightNoticeDefinitionConfigurationMapping  # type: ignore[return-value]


class TestLicenseConfiguration:
    def test___init____with_summary(self) -> None:
        summary = "My First License Summary"
        sut = LicenseDefinitionConfiguration(id="-", label="", summary=summary, text="")
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test___init____with_text(self) -> None:
        text = "My First License Text"
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text=text)
        assert sut.text[UNDETERMINED_LOCALE] == text

    def test_summary(self) -> None:
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        summary = "My First License Summary"
        sut.summary = summary
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test_text(self) -> None:
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        text = "My First License Text"
        sut.text = text
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load(self) -> None:
        summary = "My First License Summary"
        text = "My First License Text"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": summary,
            "text": text,
        }
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        sut.load(dump)
        assert sut.summary[UNDETERMINED_LOCALE] == summary
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load__with_missing_summary(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "text": "",
        }
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        with pytest.raises(HumanFacingException):
            sut.load(dump)

    async def test_load__with_missing_text(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": "",
        }
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        with pytest.raises(HumanFacingException):
            sut.load(dump)

    async def test_dump(self) -> None:
        summary = "My First License Summary"
        text = "My First License Text"
        sut = LicenseDefinitionConfiguration(
            id="-", label="", summary=summary, text=text
        )
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text


class TestLicenseDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        LicenseDefinition, LicenseDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        LicenseDefinitionConfiguration
    ]:
        return (
            LicenseDefinitionConfiguration(id="foo", label="Foo", summary="", text=""),
            LicenseDefinitionConfiguration(id="bar", label="Bar", summary="", text=""),
            LicenseDefinitionConfiguration(id="baz", label="Baz", summary="", text=""),
            LicenseDefinitionConfiguration(id="qux", label="Qux", summary="", text=""),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        LicenseDefinitionConfiguration, MachineName
    ]:
        return LicenseDefinitionConfigurationMapping


class TestEventTypeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        EventTypeDefinition, EventTypeDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        EventTypeDefinitionConfiguration
    ]:
        return (
            EventTypeDefinitionConfiguration(id="foo", label="Foo"),
            EventTypeDefinitionConfiguration(id="bar", label="Bar"),
            EventTypeDefinitionConfiguration(id="baz", label="Baz"),
            EventTypeDefinitionConfiguration(id="qux", label="Qux"),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        EventTypeDefinitionConfiguration, MachineName
    ]:
        return EventTypeDefinitionConfigurationMapping


class TestPlaceTypeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        PlaceTypeDefinition, PlaceTypeDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PlaceTypeDefinitionConfiguration
    ]:
        return (
            PlaceTypeDefinitionConfiguration(id="foo", label="Foo"),
            PlaceTypeDefinitionConfiguration(id="bar", label="Bar"),
            PlaceTypeDefinitionConfiguration(id="baz", label="Baz"),
            PlaceTypeDefinitionConfiguration(id="qux", label="Qux"),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PlaceTypeDefinitionConfiguration, MachineName
    ]:
        return PlaceTypeDefinitionConfigurationMapping


class TestPresenceRoleDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        PresenceRoleDefinition, PresenceRoleDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PresenceRoleDefinitionConfiguration
    ]:
        return (
            PresenceRoleDefinitionConfiguration(id="foo", label="Foo"),
            PresenceRoleDefinitionConfiguration(id="bar", label="Bar"),
            PresenceRoleDefinitionConfiguration(id="baz", label="Baz"),
            PresenceRoleDefinitionConfiguration(id="qux", label="Qux"),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PresenceRoleDefinitionConfiguration, MachineName
    ]:
        return PresenceRoleDefinitionConfigurationMapping


class TestGenderDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        GenderDefinition, GenderDefinitionConfiguration
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        GenderDefinitionConfiguration
    ]:
        return (
            GenderDefinitionConfiguration(id="foo", label="Foo"),
            GenderDefinitionConfiguration(id="bar", label="Bar"),
            GenderDefinitionConfiguration(id="baz", label="Baz"),
            GenderDefinitionConfiguration(id="qux", label="Qux"),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        GenderDefinitionConfiguration, MachineName
    ]:
        return GenderDefinitionConfigurationMapping


class TestProjectConfiguration:
    async def test_configuration_file_path(self, tmp_path: Path) -> None:
        configuration_file_path = tmp_path / "init.json"
        sut = ProjectConfiguration(configuration_file_path)
        assert sut.configuration_file_path == configuration_file_path

    async def test_set_configuration_file_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "init.json")
        configuration_file_path = tmp_path / "set.json"
        await sut.set_configuration_file_path(configuration_file_path)
        # Assert that setting the path to its existing value is a no-op.
        await sut.set_configuration_file_path(configuration_file_path)

    async def test_set_configuration_file_path__with_unsupported_format(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "init")
        configuration_file_path = tmp_path / "set"
        with pytest.raises(FormatError):
            await sut.set_configuration_file_path(configuration_file_path)

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

    async def test_localize_www_directory_path__monolingual(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE not in str(actual)

    async def test_localize_www_directory_path__multilingual(
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
        sut.entity_types  # noqa B018

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

    async def test_url__without_scheme_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(HumanFacingException):
            sut.url = "/"

    async def test_url__without_path_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(HumanFacingException):
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

    async def test_author__without_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert not sut.author

    async def test_author__with_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        author = "Bart"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test___init____with_logo(self, tmp_path: Path) -> None:
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

    async def test_licenses(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.licenses is sut.licenses

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

    async def test_load__should_load_minimal(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        sut.load(dump)
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert not sut.clean_urls

    async def test_load__should_load_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["name"] = name
        sut.load(dump)
        assert sut.name == name

    async def test_load__should_load_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["title"] = title
        sut.load(dump)
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_load__should_load_copyright_notice(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        copyright_notice_id = "my-first-copyright-notice"
        dump["copyright_notice"] = copyright_notice_id
        sut.load(dump)
        assert sut.copyright_notice.id == copyright_notice_id

    async def test_load__should_load_copyright_notices(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        copyright_notice_id = "my-first-copyright-notice"
        copyright_notice_label = "My First Copyright Notice"
        dump["copyright_notices"] = {
            copyright_notice_id: {
                "label": copyright_notice_label,
                "summary": "This is My First Copyright Notice.",
                "text": "My First Copyright Notice is the best copyright notice.",
            }
        }
        sut.load(dump)
        assert (
            sut.copyright_notices[copyright_notice_id].label.localize(DEFAULT_LOCALIZER)
            == copyright_notice_label
        )

    async def test_load__should_load_license(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        license_id = "my-first-license"
        dump["license"] = license_id
        sut.load(dump)
        assert sut.license.id == license_id

    async def test_load__should_load_licenses(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        license_id = "my-first-license"
        license_label = "My First License"
        dump["licenses"] = {
            license_id: {
                "label": license_label,
                "summary": "This is My First License.",
                "text": "My First License is the best license.",
            }
        }
        sut.load(dump)
        assert (
            sut.licenses[license_id].label.localize(DEFAULT_LOCALIZER) == license_label
        )

    async def test_load__should_load_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["author"] = author
        sut.load(dump)
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load__should_load_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["logo"] = str(logo)
        sut.load(dump)
        assert sut.logo == logo

    async def test_load__should_load_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["locales"] = [{"locale": locale}]
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales

    async def test_load__should_load_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["locales"] = [{"locale": locale, "alias": alias}]
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales
        actual = sut.locales[locale]
        assert actual.alias == alias

    async def test_load__should_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["clean_urls"] = clean_urls
        sut.load(dump)
        assert sut.clean_urls == clean_urls

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_load__should_load_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["debug"] = debug
        sut.load(dump)
        assert sut.debug == debug

    async def test_load__should_load_extension(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["extensions"] = {
            DummyExtension.plugin.id: {},
        }
        sut.load(dump)
        actual = sut.extensions[DummyExtension.plugin]
        assert isinstance(actual.configuration, Void)

    async def test_load__extension_with_invalid_configuration_should_raise_error(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["extensions"] = {
            DummyConfigurableExtension.plugin.id: 1337,
        }
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    @pytest.mark.parametrize(
        ("expected", "event_types_configuration"),
        [
            ({}, {}),
            ({"foo": {"label": "Foo", "description": {}}}, {"foo": {"label": "Foo"}}),
        ],
    )
    async def test_load__should_load_event_types(
        self,
        expected: DumpMapping[Dump],
        event_types_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["event_types"] = event_types_configuration
        sut.load(dump)
        if event_types_configuration:
            assert sut.dump()["event_types"] == expected

    @pytest.mark.parametrize(
        ("expected", "place_types_configuration"),
        [
            ({}, {}),
            ({"foo": {"label": "Foo", "description": {}}}, {"foo": {"label": "Foo"}}),
        ],
    )
    async def test_load__should_load_place_types(
        self,
        expected: DumpMapping[Dump],
        place_types_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["place_types"] = place_types_configuration
        sut.load(dump)
        if place_types_configuration:
            assert sut.dump()["place_types"] == expected

    @pytest.mark.parametrize(
        ("expected", "presence_roles_configuration"),
        [
            ({}, {}),
            ({"foo": {"label": "Foo", "description": {}}}, {"foo": {"label": "Foo"}}),
        ],
    )
    async def test_load__should_load_presence_roles(
        self,
        expected: DumpMapping[Dump],
        presence_roles_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["presence_roles"] = presence_roles_configuration
        sut.load(dump)
        if presence_roles_configuration:
            assert sut.dump()["presence_roles"] == expected

    @pytest.mark.parametrize(
        ("expected", "genders_configuration"),
        [
            ({}, {}),
            ({"foo": {"label": "Foo", "description": {}}}, {"foo": {"label": "Foo"}}),
        ],
    )
    async def test_load__should_load_genders(
        self,
        expected: DumpMapping[Dump],
        genders_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        dump["genders"] = genders_configuration
        sut.load(dump)
        if genders_configuration:
            assert sut.dump()["genders"] == expected

    async def test_load__should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_dump__should_dump_minimal(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump = sut.dump()
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_dump__should_dump_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.title = title
        dump = sut.dump()
        assert title == dump["title"]

    async def test_dump__should_dump_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.name = name
        dump = sut.dump()
        assert dump["name"] == name

    async def test_dump__should_dump_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.author = author
        dump = sut.dump()
        assert author == dump["author"]

    async def test_dump__should_dumpo_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.logo = logo
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["logo"] == str(logo)

    async def test_dump__should_dump_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump = sut.dump()
        assert dump["locales"] == [
            {
                "locale": locale,
                "alias": None,
            },
        ]

    async def test_dump__should_dump_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump = sut.dump()
        assert dump["locales"] == [
            {"locale": locale, "alias": alias},
        ]

    async def test_dump__should_dump_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.clean_urls = clean_urls
        dump = sut.dump()
        assert clean_urls == dump["clean_urls"]

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_dump__should_dump_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.debug = debug
        dump = sut.dump()
        assert debug == dump["debug"]

    async def test_dump__should_dump_one_extension_with_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        value = "Hello, world!"
        sut.extensions.append(
            PluginInstanceConfiguration(
                DummyConfigurableExtension.plugin,
                configuration=DummyConfiguration(value=value),
            )
        )
        dump = sut.dump()
        expected = {
            DummyConfigurableExtension.plugin.id: {
                "configuration": {
                    "value": value,
                },
            }
        }
        assert dump["extensions"] == expected

    async def test_dump__should_dump_one_extension_without_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.extensions.enable(_DummyNonConfigurableExtension)
        dump = sut.dump()
        expected: Dump = {_DummyNonConfigurableExtension.plugin.id: {}}
        assert dump["extensions"] == expected

    async def test_dump__should_dump_event_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.event_types.append(EventTypeDefinitionConfiguration(id="foo", label="Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["event_types"] == expected

    async def test_dump__should_dump_place_types(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.place_types.append(PlaceTypeDefinitionConfiguration(id="foo", label="Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["place_types"] == expected

    async def test_dump__should_dump_presence_roles(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.presence_roles.append(
            PresenceRoleDefinitionConfiguration(id="foo", label="Foo")
        )
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["presence_roles"] == expected

    async def test_dump__should_dump_genders(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.genders.append(GenderDefinitionConfiguration(id="foo", label="Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["genders"] == expected

    async def test_dump__should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_dump__should_dump_copyright_notice(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.dump()["copyright_notice"] == ProjectAuthor.plugin.id

    async def test_dump__should_dump_copyright_notices_without_items(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.dump()["copyright_notices"] == {}

    async def test_dump__should_dump_copyright_notices_with_items(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        copyright_notice_id = "my-first-copyright-notice"
        copyright_notice_label = "My First Copyright Notice"
        copyright_notice_summary = "This is My First Copyright Notice."
        copyright_notice_text = (
            "My First Copyright Notice is the best copyright notice."
        )
        sut.copyright_notices.append(
            CopyrightNoticeDefinitionConfiguration(
                id=copyright_notice_id,
                label=copyright_notice_label,
                summary=copyright_notice_summary,
                text=copyright_notice_text,
            )
        )
        assert sut.dump()["copyright_notices"] == {
            copyright_notice_id: {
                "label": copyright_notice_label,
                "summary": copyright_notice_summary,
                "text": copyright_notice_text,
                "description": {},
            }
        }

    async def test_dump__should_dump_license(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.dump()["license"] == AllRightsReserved.plugin.id

    async def test_dump__should_dump_licenses_without_items(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert sut.dump()["licenses"] == {}

    async def test_dump__should_dump_licenses_with_items(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        license_id = "my-first-license"
        license_label = "My First License"
        license_summary = "This is My First License."
        license_text = "My First License is the best license."
        sut.licenses.append(
            LicenseDefinitionConfiguration(
                id=license_id,
                label=license_label,
                summary=license_summary,
                text=license_text,
            )
        )
        assert sut.dump()["licenses"] == {
            license_id: {
                "label": license_label,
                "summary": license_summary,
                "text": license_text,
                "description": {},
            }
        }


class TestCopyrightNoticeDefinitionConfiguration:
    def test_load(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        dump: Dump = {
            "id": "hello-world",
            "label": "Hello, world!",
            "summary": summary,
            "text": text,
        }
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        sut.load(dump)
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    def test_dump(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary=summary, text=text
        )
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text

    def test_summary(self) -> None:
        summary = "My First Summary"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary=summary, text=""
        )
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary

    def test_text(self) -> None:
        text = "My First Summary"
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=text
        )
        assert sut.text.localize(DEFAULT_LOCALIZER) == text


class TestLicenseDefinitionConfiguration:
    def test_load(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        dump: Dump = {
            "id": "hello-world",
            "label": "Hello, world!",
            "summary": summary,
            "text": text,
        }
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        sut.load(dump)
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    def test_dump(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        sut = LicenseDefinitionConfiguration(
            id="-", label="", summary=summary, text=text
        )
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text

    def test_summary(self) -> None:
        summary = "My First Summary"
        sut = LicenseDefinitionConfiguration(id="-", label="", summary=summary, text="")
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary

    def test_text(self) -> None:
        text = "My First Summary"
        sut = LicenseDefinitionConfiguration(id="-", label="", summary="", text=text)
        assert sut.text.localize(DEFAULT_LOCALIZER) == text
