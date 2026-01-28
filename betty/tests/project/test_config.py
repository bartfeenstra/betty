from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from babel import Locale
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, LocaleLike
from betty.locale.localizable.plain import Plain
from betty.model import EntityDefinition
from betty.plugin.discovery.static import StaticDiscovery
from betty.project.config import (
    CopyrightNoticeDefinitionConfiguration,
    EntityTypeConfiguration,
    EventTypeDefinitionConfiguration,
    GenderDefinitionConfiguration,
    LicenseDefinitionConfiguration,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    PlaceTypeDefinitionConfiguration,
    PresenceRoleDefinitionConfiguration,
    ProjectConfiguration,
)
from betty.service.level.universal import universe
from betty.test_utils.config import ConfigurationTestBase
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
)
from betty.test_utils.config.collections.mapping import (
    OrderedConfigurationMappingTestBase,
)
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.model import DummyEntityOne, DummyNonPublicFacingEntityOne

if TYPE_CHECKING:
    from betty.portable import PortableData
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseSutConfigurationKeys,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


@ExtensionDefinition("dummy-non-configurable", label=DUMMY_LOCALIZABLE)
class _DummyNonConfigurableExtension(Extension):
    pass


class TestLocaleConfiguration(ConfigurationTestBase[LocaleConfiguration]):
    sut_cls = LocaleConfiguration

    async def test_locale(self) -> None:
        locale = Locale("nl")
        sut = LocaleConfiguration(locale)
        assert sut.locale is locale

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
        portable: PortableData = {}
        with pytest.raises(HumanFacingException):
            LocaleConfiguration.load(portable)

    async def test_load__with_locale(self) -> None:
        portable: PortableData = {
            "locale": DEFAULT_LOCALE_TAG,
        }
        sut = LocaleConfiguration.load(portable)
        assert sut.locale == DEFAULT_LOCALE

    async def test_load__with_alias(self) -> None:
        portable: PortableData = {
            "locale": "nl-NL",
            "alias": "my-first-alias",
        }
        sut = LocaleConfiguration.load(portable)
        assert sut.alias == "my-first-alias"

    async def test_dump__should_dump_minimal(self) -> None:
        sut = LocaleConfiguration("nl-NL")
        expected = {
            "locale": "nl-NL",
        }
        assert sut.dump() == expected

    async def test_dump__should_dump_alias(self) -> None:
        sut = LocaleConfiguration("nl-NL", alias="nl")
        expected = {"locale": "nl-NL", "alias": "nl"}
        assert sut.dump() == expected


LocaleConfigurationMappingTestNewSut = ConfigurationCollectionTestBaseNewSut[
    LocaleConfiguration, Locale, LocaleLike
]


class TestLocaleConfigurationMapping(
    OrderedConfigurationMappingTestBase[
        LocaleConfigurationMapping, Locale, LocaleLike, LocaleConfiguration
    ]
):
    sut_cls = LocaleConfigurationMapping

    @override
    @pytest.fixture
    def new_sut(self) -> LocaleConfigurationMappingTestNewSut:
        return LocaleConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[Locale]:
        return (
            Locale("en"),
            Locale("nl"),
            Locale("uk"),
            Locale("fr"),
        )

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
    def test___delitem__(
        self,
        new_sut: LocaleConfigurationMappingTestNewSut,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:  # ty:ignore[invalid-method-override]
        sut = new_sut([sut_configurations[0]])
        del sut[sut_configurations[0].locale]
        with pytest.raises(KeyError):
            sut[sut_configurations[0].locale]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    def test___delitem____with_locale(
        self,
        new_sut: LocaleConfigurationMappingTestNewSut,
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
    def test_replace__without_items(self, sut: LocaleConfigurationMapping) -> None:  # ty:ignore[invalid-method-override]
        sut.clear()
        assert len(sut) == 1
        sut.replace()
        assert len(sut) == 1

    @override
    def test_replace__with_items(
        self,
        sut: LocaleConfigurationMapping,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:  # ty:ignore[invalid-method-override]
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


class TestEntityTypeConfiguration(DataTestBase[EntityTypeConfiguration]):
    sut_cls = EntityTypeConfiguration

    async def test_entity_type__with___init___entity_type(self) -> None:
        entity_type = DummyEntityOne
        sut = EntityTypeConfiguration(entity_type=entity_type)
        assert sut.entity_type == entity_type.plugin().id

    async def test_entity_type__with___init___entity_type_id(self) -> None:
        entity_type_id = DummyEntityOne.plugin().id
        sut = EntityTypeConfiguration(entity_type=entity_type_id)
        assert sut.entity_type == entity_type_id

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(entity_type=DummyEntityOne)
        sut.generate_html_list = generate_html_list
        assert sut.generate_html_list == generate_html_list

    async def test_hydrate__with_generate_html_list_with_non_public_facing_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityTypeConfiguration(
            entity_type=DummyNonPublicFacingEntityOne, generate_html_list=True
        )
        with (
            EntityDefinition.type().override_discovery(
                StaticDiscovery(DummyNonPublicFacingEntityOne)
            ),
            pytest.raises(HumanFacingException),
        ):
            await sut.hydrate(universe)


class TestProjectConfiguration(DataTestBase[ProjectConfiguration]):
    sut_cls = ProjectConfiguration

    async def test_lifetime_threshold(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    async def test_locales(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert DEFAULT_LOCALE in sut.locales

    async def test_extensions(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.extensions) == 0

    async def test_entity_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.entity_types  # noqa: B018

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.debug = debug
        assert sut.debug == debug

    async def test_title(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        title = Plain("My First Betty Site")
        sut.title = title
        assert sut.title is title

    async def test_name(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        name = "my-first-betty-site"
        sut.name = name
        assert sut.name == name

    async def test_url(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    async def test_url__without_scheme_should_error(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        with pytest.raises(HumanFacingException):
            sut.url = "/"

    async def test_url__without_path_should_error(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
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
    async def test_base_url(self, expected: str, url: str) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
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
    async def test_root_path(self, expected: str, url: str) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.url = url
        assert sut.root_path == expected

    async def test_clean_urls(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert sut.clean_urls == clean_urls

    async def test_author__without_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.author is None

    async def test_author__with_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        author = Plain("Bart")
        sut.author = author
        assert sut.author is author

    async def test___init____with_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(logo=logo, title="Betty", url="https://example.com")
        assert sut.logo == logo

    async def test_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.logo = logo
        assert sut.logo == logo

    async def test_copyright_notices(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.copyright_notices is sut.copyright_notices

    async def test_licenses(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.licenses is sut.licenses

    async def test_event_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.event_types is sut.event_types

    async def test_place_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.place_types is sut.place_types

    async def test_presence_roles(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.presence_roles is sut.presence_roles

    async def test_genders(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.genders is sut.genders


class TestCopyrightNoticeDefinitionConfiguration:
    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=DUMMY_LOCALIZABLE
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = CopyrightNoticeDefinitionConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=DUMMY_LOCALIZABLE, text=text
        )
        assert sut.text is text

    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-copyright-notice"
        label = Plain("-")
        summary = Plain("-")
        text = Plain("-")
        sut = CopyrightNoticeDefinitionConfiguration(
            id=plugin_id,
            label=label,
            summary=summary,
            text=text,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.cls().summary is summary
        assert plugin.cls().text is text

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = CopyrightNoticeDefinitionConfiguration(
            id="my-first-copyright-notice",
            label=DUMMY_LOCALIZABLE,
            description=description,
            summary=DUMMY_LOCALIZABLE,
            text=DUMMY_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description


class TestLicenseDefinitionConfiguration:
    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = LicenseDefinitionConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=DUMMY_LOCALIZABLE
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = LicenseDefinitionConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=DUMMY_LOCALIZABLE, text=text
        )
        assert sut.text is text

    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-license"
        label = Plain("-")
        summary = Plain("-")
        text = Plain("-")
        sut = LicenseDefinitionConfiguration(
            id=plugin_id,
            label=label,
            summary=summary,
            text=text,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.cls().summary is summary
        assert plugin.cls().text is text

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = LicenseDefinitionConfiguration(
            id="my-first-license",
            label=DUMMY_LOCALIZABLE,
            description=description,
            summary=DUMMY_LOCALIZABLE,
            text=DUMMY_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description


class TestGenderDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-gender"
        label = Plain("-")
        label_plural = Plain("-")
        sut = GenderDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = GenderDefinitionConfiguration(
            id="my-first-gender",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description


class TestPlaceTypeDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-place-type"
        label = Plain("-")
        label_plural = Plain("-")
        sut = PlaceTypeDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = PlaceTypeDefinitionConfiguration(
            id="my-first-place-type",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description


class TestPresenceRoleDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-presence-role"
        label = Plain("-")
        label_plural = Plain("-")
        sut = PresenceRoleDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = PresenceRoleDefinitionConfiguration(
            id="my-first-presence-role",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description


class TestEventTypeDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-event-type"
        label = Plain("-")
        label_plural = Plain("-")
        sut = EventTypeDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        comes_before = {"my-first-other-event-type"}
        comes_after = {"my-second-other-event-type"}
        sut = EventTypeDefinitionConfiguration(
            id="my-first-event-type",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
            comes_before=comes_before,
            comes_after=comes_after,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description
        assert plugin.comes_before == comes_before
        assert plugin.comes_after == comes_after
