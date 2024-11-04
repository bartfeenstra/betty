from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventType
from betty.ancestry.gender import Gender
from betty.ancestry.place_type import PlaceType
from betty.ancestry.presence_role import PresenceRole
from betty.assertion.error import AssertionFailed
from betty.copyright_notice import CopyrightNotice
from betty.copyright_notice.copyright_notices import ProjectAuthor
from betty.license import License
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.model import UserFacingEntity
from betty.plugin.config import (
    PluginConfiguration,
    PluginInstanceConfiguration,
)
from betty.plugin.static import StaticPluginRepository
from betty.project.config import (
    LocaleConfiguration,
    LocaleConfigurationMapping,
    ExtensionInstanceConfigurationMapping,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    EventTypeConfigurationMapping,
    PresenceRoleConfigurationMapping,
    PlaceTypeConfigurationMapping,
    GenderConfigurationMapping,
    CopyrightNoticeConfigurationMapping,
    CopyrightNoticeConfiguration,
    LicenseConfiguration,
    LicenseConfigurationMapping,
)
from betty.project.config import ProjectConfiguration
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.model import DummyEntity
from betty.test_utils.plugin.config import PluginConfigurationMappingTestBase
from betty.test_utils.project.extension import (
    DummyExtension,
    DummyConfigurableExtension,
)
from betty.typing import Void

if TYPE_CHECKING:
    from betty.config import Configuration
    from betty.serde.dump import Dump, DumpMapping
    from pytest_mock import MockerFixture
    from pathlib import Path


class _DummyNonConfigurableExtension(DummyExtension):
    pass


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
        expected = {"locale": "nl-NL", "alias": None}
        assert sut.dump() == expected

    async def test_dump_should_dump_alias(self) -> None:
        sut = LocaleConfiguration("nl-NL", alias="nl")
        expected = {"locale": "nl-NL", "alias": "nl"}
        assert sut.dump() == expected


class TestLocaleConfigurationMapping(
    ConfigurationMappingTestBase[str, LocaleConfiguration]
):
    @override
    async def get_sut(
        self, configurations: Iterable[Configuration] | None = None
    ) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping(configurations)  # type: ignore[arg-type]

    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return ("en", "nl", "uk", "fr")

    @override
    async def get_configurations(
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

    async def test___delitem__(self) -> None:
        configurations = await self.get_configurations()
        sut = await self.get_sut([configurations[0]])
        del sut[configurations[0].locale]
        with pytest.raises(KeyError):
            sut[configurations[0].locale]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    async def test___delitem___with_locale(self) -> None:
        configurations = await self.get_configurations()
        sut = await self.get_sut([configurations[0], configurations[1]])
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
        sut = await self.get_sut()
        sut.clear()
        assert len(sut) == 1
        await self.get_configurations()
        sut.replace()
        assert len(sut) == 1

    @override
    async def test_replace_with_items(self) -> None:
        sut = await self.get_sut()
        sut.clear()
        assert len(sut) == 1
        configurations = await self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)

    async def test_multilingual_with_one_configuration(self) -> None:
        sut = await self.get_sut()
        assert not sut.multilingual

    async def test_multilingual_with_multiple_configurations(self) -> None:
        sut = await self.get_sut()
        sut.replace(*await self.get_configurations())
        assert sut.multilingual


class ExtensionInstanceConfigurationMappingTestExtension0(DummyExtension):
    pass


class ExtensionInstanceConfigurationMappingTestExtension1(DummyExtension):
    pass


class ExtensionInstanceConfigurationMappingTestExtension2(DummyExtension):
    pass


class ExtensionInstanceConfigurationMappingTestExtension3(DummyExtension):
    pass


class TestExtensionInstanceConfigurationMapping(
    ConfigurationMappingTestBase[MachineName, PluginInstanceConfiguration]
):
    @override
    def get_configuration_keys(
        self,
    ) -> tuple[MachineName, MachineName, MachineName, MachineName]:
        return (
            ExtensionInstanceConfigurationMappingTestExtension0.plugin_id(),
            ExtensionInstanceConfigurationMappingTestExtension1.plugin_id(),
            ExtensionInstanceConfigurationMappingTestExtension2.plugin_id(),
            ExtensionInstanceConfigurationMappingTestExtension3.plugin_id(),
        )

    @override
    async def get_sut(
        self,
        configurations: Iterable[PluginInstanceConfiguration] | None = None,
    ) -> ExtensionInstanceConfigurationMapping:
        return ExtensionInstanceConfigurationMapping(configurations)

    @override
    async def get_configurations(
        self,
    ) -> tuple[
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
    ]:
        return (
            PluginInstanceConfiguration(self.get_configuration_keys()[0]),
            PluginInstanceConfiguration(self.get_configuration_keys()[1]),
            PluginInstanceConfiguration(self.get_configuration_keys()[2]),
            PluginInstanceConfiguration(self.get_configuration_keys()[3]),
        )

    def test_enable(self) -> None:
        sut = ExtensionInstanceConfigurationMapping()
        sut.enable(DummyExtension)
        assert DummyExtension in sut


class EntityTypeConfigurationTestEntityOne(UserFacingEntity, DummyEntity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity, DummyEntity):
    pass


class TestEntityTypeConfiguration:
    async def test_id_with___init___entity_type(self) -> None:
        entity_type = EntityTypeConfigurationTestEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert sut.id == entity_type.plugin_id()

    async def test_id_with___init___entity_type_id(self) -> None:
        entity_type_id = EntityTypeConfigurationTestEntityOne.plugin_id()
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
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.generate_html_list = generate_html_list
        assert sut.generate_html_list == generate_html_list

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
            "id": EntityTypeConfigurationTestEntityOne.plugin_id(),
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
            "id": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)
        assert sut.generate_html_list == generate_html_list

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = {
            "id": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(
            EntityTypeConfigurationTestEntityOne, generate_html_list=False
        )
        expected = {
            "id": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_validate_with_generate_html_list_without_user_facing_entity_type_should_error(
        self,
    ) -> None:
        plugin = DummyEntity
        sut = EntityTypeConfiguration(plugin, generate_html_list=True)
        with pytest.raises(AssertionFailed):
            await sut.validate(StaticPluginRepository(plugin))


class EntityTypeConfigurationMappingTestEntity0(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity1(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity2(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity3(DummyEntity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[MachineName, EntityTypeConfiguration]
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
    ) -> tuple[MachineName, MachineName, MachineName, MachineName]:
        return (
            EntityTypeConfigurationMappingTestEntity0.plugin_id(),
            EntityTypeConfigurationMappingTestEntity1.plugin_id(),
            EntityTypeConfigurationMappingTestEntity2.plugin_id(),
            EntityTypeConfigurationMappingTestEntity3.plugin_id(),
        )

    async def get_sut(
        self, configurations: Iterable[EntityTypeConfiguration] | None = None
    ) -> EntityTypeConfigurationMapping:
        return EntityTypeConfigurationMapping(configurations)

    async def get_configurations(
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

    async def test_validate_with_item_error_should_error(self) -> None:
        plugin = DummyEntity
        sut = EntityTypeConfigurationMapping(
            [EntityTypeConfiguration(plugin, generate_html_list=True)]
        )
        with pytest.raises(AssertionFailed):
            await sut.validate(StaticPluginRepository(plugin))


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
    PluginConfigurationMappingTestBase[CopyrightNotice, CopyrightNoticeConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
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
    async def get_sut(
        self, configurations: Iterable[CopyrightNoticeConfiguration] | None = None
    ) -> CopyrightNoticeConfigurationMapping:
        return CopyrightNoticeConfigurationMapping(configurations)


class TestLicenseConfiguration:
    def test___init___with_summary(self) -> None:
        summary = "My First License Summary"
        sut = LicenseConfiguration("-", "", summary=summary, text="")
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test___init___with_text(self) -> None:
        text = "My First License Text"
        sut = LicenseConfiguration("-", "", summary="", text=text)
        assert sut.text[UNDETERMINED_LOCALE] == text

    def test_summary(self) -> None:
        sut = LicenseConfiguration("-", "", summary="", text="")
        summary = "My First License Summary"
        sut.summary = summary
        assert sut.summary[UNDETERMINED_LOCALE] == summary

    def test_text(self) -> None:
        sut = LicenseConfiguration("-", "", summary="", text="")
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
        sut = LicenseConfiguration("-", "", summary="", text="")
        sut.load(dump)
        assert sut.summary[UNDETERMINED_LOCALE] == summary
        assert sut.text[UNDETERMINED_LOCALE] == text

    async def test_load_with_missing_summary(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "text": "",
        }
        sut = LicenseConfiguration("-", "", summary="", text="")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_load_with_missing_text(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "summary": "",
        }
        sut = LicenseConfiguration("-", "", summary="", text="")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_dump(self) -> None:
        summary = "My First License Summary"
        text = "My First License Text"
        sut = LicenseConfiguration("-", "", summary=summary, text=text)
        dump = sut.dump()
        assert dump["summary"] == summary
        assert dump["text"] == text


class TestLicenseConfigurationMapping(
    PluginConfigurationMappingTestBase[License, LicenseConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
        self,
    ) -> tuple[
        LicenseConfiguration,
        LicenseConfiguration,
        LicenseConfiguration,
        LicenseConfiguration,
    ]:
        return (
            LicenseConfiguration("foo", "Foo", summary="", text=""),
            LicenseConfiguration("bar", "Bar", summary="", text=""),
            LicenseConfiguration("baz", "Baz", summary="", text=""),
            LicenseConfiguration("qux", "Qux", summary="", text=""),
        )

    @override
    async def get_sut(
        self, configurations: Iterable[LicenseConfiguration] | None = None
    ) -> LicenseConfigurationMapping:
        return LicenseConfigurationMapping(configurations)


class TestEventTypeConfigurationMapping(
    PluginConfigurationMappingTestBase[EventType, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
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
    async def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> EventTypeConfigurationMapping:
        return EventTypeConfigurationMapping(configurations)


class TestPlaceTypeConfigurationMapping(
    PluginConfigurationMappingTestBase[PlaceType, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
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
    async def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> PlaceTypeConfigurationMapping:
        return PlaceTypeConfigurationMapping(configurations)


class TestPresenceRoleConfigurationMapping(
    PluginConfigurationMappingTestBase[PresenceRole, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
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
    async def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> PresenceRoleConfigurationMapping:
        return PresenceRoleConfigurationMapping(configurations)


class TestGenderConfigurationMapping(
    PluginConfigurationMappingTestBase[Gender, PluginConfiguration]
):
    @override
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    @override
    async def get_configurations(
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
    async def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> GenderConfigurationMapping:
        return GenderConfigurationMapping(configurations)


class TestProjectConfiguration:
    async def test_configuration_file_path(self, tmp_path: Path) -> None:
        old_configuration_file_path = tmp_path / "betty.json"
        sut = await ProjectConfiguration.new(old_configuration_file_path)
        assert sut.configuration_file_path == old_configuration_file_path
        new_configuration_file_path = tmp_path / "betty.yaml"
        sut.configuration_file_path = new_configuration_file_path
        assert sut.configuration_file_path == new_configuration_file_path
        # Assert that setting the path to its existing value is a no-op.
        sut.configuration_file_path = new_configuration_file_path
        assert sut.configuration_file_path == new_configuration_file_path

    async def test_project_directory_path(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.project_directory_path == tmp_path

    async def test_output_directory_path(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert tmp_path in sut.output_directory_path.parents

    async def test_assets_directory_path(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert tmp_path in sut.assets_directory_path.parents

    async def test_www_directory_path(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert tmp_path in sut.www_directory_path.parents

    async def test_localize_www_directory_path_monolingual(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE not in str(actual)

    async def test_localize_www_directory_path_multilingual(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.locales.append(LocaleConfiguration("nl-NL"))
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE in str(actual)

    async def test_lifetime_threshold(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    async def test_locales(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert DEFAULT_LOCALE in sut.locales

    async def test_extensions(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert len(sut.extensions) == 0

    async def test_entity_types(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert len(sut.entity_types)

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.debug = debug
        assert sut.debug == debug

    async def test_title(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        title = "My First Betty Site"
        sut.title = title
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_name(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        name = "my-first-betty-site"
        sut.name = name
        assert sut.name == name

    async def test_url(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    async def test_url_without_scheme_should_error(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        with pytest.raises(AssertionFailed):
            sut.url = "/"

    async def test_url_without_path_should_error(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.url = url
        assert sut.root_path == expected

    async def test_clean_urls(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert sut.clean_urls == clean_urls

    async def test_author_without_author(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert not sut.author

    async def test_author_with_author(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        author = "Bart"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test___init___with_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json", logo=logo)
        assert sut.logo == logo

    async def test_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.logo = logo
        assert sut.logo == logo

    async def test_copyright_notices(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.copyright_notices is sut.copyright_notices

    async def test_licenses(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.licenses is sut.licenses

    async def test_event_types(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.event_types is sut.event_types

    async def test_place_types(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.place_types is sut.place_types

    async def test_presence_roles(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.presence_roles is sut.presence_roles

    async def test_genders(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.genders is sut.genders

    async def test_load_should_load_minimal(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        sut.load(dump)
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert not sut.clean_urls

    async def test_load_should_load_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["name"] = name
        sut.load(dump)
        assert sut.name == name

    async def test_load_should_load_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["title"] = title
        sut.load(dump)
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_load_should_load_copyright_notice(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        copyright_notice_id = "my-first-copyright-notice"
        dump["copyright_notice"] = copyright_notice_id
        sut.load(dump)
        assert sut.copyright_notice.id == copyright_notice_id

    async def test_load_should_load_copyright_notices(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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

    async def test_load_should_load_license(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        license_id = "my-first-license"
        dump["license"] = license_id
        sut.load(dump)
        assert sut.license.id == license_id

    async def test_load_should_load_licenses(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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

    async def test_load_should_load_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["author"] = author
        sut.load(dump)
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load_should_load_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["logo"] = str(logo)
        sut.load(dump)
        assert sut.logo == logo

    async def test_load_should_load_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["locales"] = [{"locale": locale}]
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales

    async def test_load_should_load_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["locales"] = [{"locale": locale, "alias": alias}]
        sut.load(dump)
        assert len(sut.locales) == 1
        assert locale in sut.locales
        actual = sut.locales[locale]
        assert actual.alias == alias

    async def test_load_should_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
    async def test_load_should_load_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["debug"] = debug
        sut.load(dump)
        assert sut.debug == debug

    async def test_load_should_load_extension(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(DummyExtension),
        )
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["extensions"] = {
            DummyExtension.plugin_id(): {},
        }
        sut.load(dump)
        actual = sut.extensions[DummyExtension]
        assert actual.configuration is Void

    async def test_load_extension_with_invalid_configuration_should_raise_error(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["extensions"] = {
            DummyConfigurableExtension.plugin_id(): 1337,
        }
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    @pytest.mark.parametrize(
        ("expected", "event_types_configuration"),
        [
            ({}, {}),
            ({"foo": {"label": "Foo", "description": {}}}, {"foo": {"label": "Foo"}}),
        ],
    )
    async def test_load_should_load_event_types(
        self,
        expected: DumpMapping[Dump],
        event_types_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
    async def test_load_should_load_place_types(
        self,
        expected: DumpMapping[Dump],
        place_types_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
    async def test_load_should_load_presence_roles(
        self,
        expected: DumpMapping[Dump],
        presence_roles_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
    async def test_load_should_load_genders(
        self,
        expected: DumpMapping[Dump],
        genders_configuration: DumpMapping[Dump],
        tmp_path: Path,
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        dump["genders"] = genders_configuration
        sut.load(dump)
        if genders_configuration:
            assert sut.dump()["genders"] == expected

    async def test_load_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_should_dump_minimal(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        dump = sut.dump()
        assert sut.url == dump["url"]
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_dump_should_dump_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.title = title
        dump = sut.dump()
        assert title == dump["title"]

    async def test_dump_should_dump_name(self, tmp_path: Path) -> None:
        name = "my-first-betty-site"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.name = name
        dump = sut.dump()
        assert dump["name"] == name

    async def test_dump_should_dump_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.author = author
        dump = sut.dump()
        assert author == dump["author"]

    async def test_dump_should_dumpo_logo(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.logo = logo
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["logo"] == str(logo)

    async def test_dump_should_dump_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump = sut.dump()
        assert dump["locales"] == [
            {
                "locale": locale,
                "alias": None,
            },
        ]

    async def test_dump_should_dump_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump = sut.dump()
        assert dump["locales"] == [
            {"locale": locale, "alias": alias},
        ]

    async def test_dump_should_dump_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
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
    async def test_dump_should_dump_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.debug = debug
        dump = sut.dump()
        assert debug == dump["debug"]

    async def test_dump_should_dump_one_extension_with_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        value = "Hello, world!"
        sut.extensions.append(
            PluginInstanceConfiguration(
                DummyConfigurableExtension,
                configuration=DummyConfiguration(value=value),
            )
        )
        dump = sut.dump()
        expected = {
            DummyConfigurableExtension.plugin_id(): {
                "configuration": {
                    "value": value,
                },
            }
        }
        assert dump["extensions"] == expected

    async def test_dump_should_dump_one_extension_without_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.extensions.enable(_DummyNonConfigurableExtension)
        dump = sut.dump()
        expected: Dump = {_DummyNonConfigurableExtension.plugin_id(): {}}
        assert dump["extensions"] == expected

    async def test_dump_should_dump_event_types(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.event_types.append(PluginConfiguration("foo", "Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["event_types"] == expected

    async def test_dump_should_dump_place_types(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.place_types.append(PluginConfiguration("foo", "Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["place_types"] == expected

    async def test_dump_should_dump_presence_roles(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.presence_roles.append(PluginConfiguration("foo", "Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["presence_roles"] == expected

    async def test_dump_should_dump_genders(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        sut.genders.append(PluginConfiguration("foo", "Foo"))
        dump = sut.dump()
        expected: DumpMapping[Dump] = {
            "foo": {
                "label": "Foo",
                "description": {},
            }
        }
        assert dump["genders"] == expected

    async def test_dump_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_should_dump_copyright_notice(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.dump()["copyright_notice"] == ProjectAuthor.plugin_id()

    async def test_dump_should_dump_copyright_notices_without_items(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.dump()["copyright_notices"] == {}

    async def test_dump_should_dump_copyright_notices_with_items(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        copyright_notice_id = "my-first-copyright-notice"
        copyright_notice_label = "My First Copyright Notice"
        copyright_notice_summary = "This is My First Copyright Notice."
        copyright_notice_text = (
            "My First Copyright Notice is the best copyright notice."
        )
        sut.copyright_notices.append(
            CopyrightNoticeConfiguration(
                copyright_notice_id,
                copyright_notice_label,
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

    async def test_dump_should_dump_license(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.dump()["license"] == AllRightsReserved.plugin_id()

    async def test_dump_should_dump_licenses_without_items(
        self, tmp_path: Path
    ) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        assert sut.dump()["licenses"] == {}

    async def test_dump_should_dump_licenses_with_items(self, tmp_path: Path) -> None:
        sut = await ProjectConfiguration.new(tmp_path / "betty.json")
        license_id = "my-first-license"
        license_label = "My First License"
        license_summary = "This is My First License."
        license_text = "My First License is the best license."
        sut.licenses.append(
            LicenseConfiguration(
                license_id, license_label, summary=license_summary, text=license_text
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
