from __future__ import annotations

from pathlib import Path

import pytest
from babel import Locale

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.plain import Plain
from betty.model import EntityDefinition
from betty.project.data import (
    EntityTypeConfiguration,
    ProjectConfiguration,
    ProjectLocale,
)
from betty.service.level import ServiceLevel
from betty.test_utils.data import DataTestBase
from betty.test_utils.model import DummyEntityOne, DummyNonPublicFacingEntityOne


class TestProjectLocale(DataTestBase[ProjectLocale]):
    sut_cls = ProjectLocale

    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = ProjectLocale(locale)
        assert sut.locale is locale

    def test_alias(self) -> None:
        alias = "nl"
        sut = ProjectLocale(
            DEFAULT_LOCALE,
            alias=alias,
        )
        assert sut.alias == alias

    def test_alias__invalid(self) -> None:
        alias = "nl/NL"
        with pytest.raises(HumanFacingException):
            ProjectLocale("nl-NL", alias=alias)

    def test_slug__without_alias(self) -> None:
        locale = "nl-NL"
        sut = ProjectLocale(locale)
        assert sut.slug == locale

    def test_slug__with_alias(self) -> None:
        alias = "my-first-locale"
        sut = ProjectLocale("nl-NL", alias=alias)
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

    async def test_validate__with_generate_html_list_with_non_public_facing_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityTypeConfiguration(
            entity_type=DummyNonPublicFacingEntityOne, generate_html_list=True
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(
                ServiceLevel(
                    plugins={EntityDefinition: [DummyNonPublicFacingEntityOne]}
                )
            )


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

    def test_roles(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.roles is sut.roles

    def test_genders(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.genders is sut.genders
