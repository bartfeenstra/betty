from __future__ import annotations

from pathlib import Path

import pytest

from betty.exception import HumanFacingException
from betty.locale.localizable.plain import Plain
from betty.project.data import (
    ProjectConfiguration,
)
from betty.test_utils.data import DataTestBase
from betty.test_utils.entity import DummyEntityOne


class TestProjectConfiguration(DataTestBase[ProjectConfiguration]):
    sut_cls = ProjectConfiguration

    def test_lifetime_threshold(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    def test_locales(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert not sut.locales

    async def test_enrichers(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.enrichers) == 0

    async def test_extensions(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.extensions) == 0

    async def test_generate_entity_list_html(self) -> None:
        sut = ProjectConfiguration(
            generate_entity_list_html=[DummyEntityOne],
            title="Betty",
            url="https://example.com",
        )
        assert sut.generate_entity_list_html is not None
        assert list(sut.generate_entity_list_html) == [DummyEntityOne.plugin().id]

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

    async def test_loaders(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.loaders) == 0

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
        assert sut.logo is logo

    def test_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.logo = logo
        assert sut.logo is logo

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
