from __future__ import annotations

from pathlib import Path

import pytest
from babel import Locale

from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.plain import Plain
from betty.model import EntityDefinition
from betty.project.config import (
    CopyrightNoticeDefinitionConfiguration,
    EntityTypeConfiguration,
    EventTypeDefinitionConfiguration,
    GenderDefinitionConfiguration,
    LicenseDefinitionConfiguration,
    LocaleConfiguration,
    PlaceTypeDefinitionConfiguration,
    PresenceRoleDefinitionConfiguration,
    ProjectConfiguration,
)
from betty.service.level import universe
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.model import DummyEntityOne, DummyNonPublicFacingEntityOne


@ExtensionDefinition("dummy-non-configurable", label=DUMMY_LOCALIZABLE)
class _DummyNonConfigurableExtension(Extension):
    pass


class TestLocaleConfiguration(DataTestBase[LocaleConfiguration]):
    sut_cls = LocaleConfiguration

    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = LocaleConfiguration(locale)
        assert sut.locale is locale

    def test_alias(self) -> None:
        alias = "nl"
        sut = LocaleConfiguration(
            DEFAULT_LOCALE,
            alias=alias,
        )
        assert sut.alias == alias

    def test_alias__invalid(self) -> None:
        alias = "nl/NL"
        with pytest.raises(HumanFacingException):
            LocaleConfiguration("nl-NL", alias=alias)

    def test_slug__without_alias(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.slug == locale

    def test_slug__with_alias(self) -> None:
        alias = "my-first-locale"
        sut = LocaleConfiguration("nl-NL", alias=alias)
        assert sut.slug == alias


class TestEntityTypeConfiguration(DataTestBase[EntityTypeConfiguration]):
    sut_cls = EntityTypeConfiguration

    def test_entity_type__with___init___entity_type(self) -> None:
        entity_type = DummyEntityOne
        sut = EntityTypeConfiguration(entity_type=entity_type)
        assert sut.entity_type == entity_type.plugin().id

    def test_entity_type__with___init___entity_type_id(self) -> None:
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
    def test_generate_html_list(self, generate_html_list: bool) -> None:
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
            EntityDefinition.type().discoverer.override(DummyNonPublicFacingEntityOne),
            pytest.raises(HumanFacingException),
        ):
            await sut.hydrate(services=universe)


class TestProjectConfiguration(DataTestBase[ProjectConfiguration]):
    sut_cls = ProjectConfiguration

    def test_lifetime_threshold(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    def test_locales(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert DEFAULT_LOCALE in sut.locales

    def test_default_locale(self) -> None:
        default_locale = Locale("uk")
        sut = ProjectConfiguration(
            title="Betty",
            url="https://example.com",
            locales=[default_locale, Locale("nl", "NL")],
        )
        assert sut.default_locale.locale is default_locale

    def test_multilingual__not_multilingual(self) -> None:
        sut = ProjectConfiguration(
            title="Betty", url="https://example.com", locales=[Locale("uk")]
        )
        assert not sut.multilingual

    def test_multilingual__multilingual(self) -> None:
        sut = ProjectConfiguration(
            title="Betty",
            url="https://example.com",
            locales=[Locale("uk"), Locale("nl", "NL")],
        )
        assert sut.multilingual

    async def test_extensions(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.extensions) == 0

    def test_entity_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.entity_types  # noqa: B018

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    def test_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.debug = debug
        assert sut.debug == debug

    def test_title(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        title = Plain("My First Betty Site")
        sut.title = title
        assert sut.title is title

    def test_name(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        name = "my-first-betty-site"
        sut.name = name
        assert sut.name == name

    def test_url(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    def test_url__without_scheme_should_error(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        with pytest.raises(HumanFacingException):
            sut.url = "/"

    def test_url__without_path_should_error(self) -> None:
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
    def test_base_url(self, expected: str, url: str) -> None:
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
    def test_root_path(self, expected: str, url: str) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.url = url
        assert sut.root_path == expected

    def test_clean_urls(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert sut.clean_urls == clean_urls

    def test_author__without_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.author is None

    def test_author__with_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        author = Plain("Bart")
        sut.author = author
        assert sut.author is author

    def test___init____with_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(logo=logo, title="Betty", url="https://example.com")
        assert sut.logo == logo

    def test_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.logo = logo
        assert sut.logo == logo

    def test_copyright_notices(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.copyright_notices is sut.copyright_notices

    def test_licenses(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.licenses is sut.licenses

    def test_event_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.event_types is sut.event_types

    def test_place_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.place_types is sut.place_types

    def test_presence_roles(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.presence_roles is sut.presence_roles

    def test_genders(self) -> None:
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
