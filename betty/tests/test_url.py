from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry import Person, Place, File, Source, Name, Event, Citation
from betty.ancestry.event_type import Death
from betty.model import UserFacingEntity
from betty.project import LocaleConfiguration, Project
from betty.test_utils.model import DummyEntity
from betty.url import (
    LocalizedPathUrlGenerator,
    _EntityUrlGenerator,
    ProjectUrlGenerator,
)

if TYPE_CHECKING:
    from betty.app import App
    from betty.locale import Localey


class TestLocalizedPathUrlGenerator:
    @pytest.mark.parametrize(
        "resource",
        [
            "/",
            "/index.html",
            "example",
            "/example",
            "example/",
            "/example/",
            "example/index.html",
            "/example/index.html",
        ],
    )
    async def test_supports(self, new_temporary_app: App, resource: str) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = LocalizedPathUrlGenerator(project)
            assert sut.supports(resource)

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            ("", "/"),
            ("/index.html", "/index.html"),
            ("/example", "example"),
            ("/example", "/example"),
            ("/example", "example/"),
            ("/example", "/example/"),
            ("/example/index.html", "example/index.html"),
            ("/example/index.html", "/example/index.html"),
        ],
    )
    async def test_generate(
        self, expected: str, new_temporary_app: App, resource: str
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = LocalizedPathUrlGenerator(project)
            assert sut.generate(resource, "text/html") == expected

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            ("", "index.html"),
            ("", "/index.html"),
            ("/example", "example/index.html"),
            ("/example", "/example/index.html"),
        ],
    )
    async def test_generate_with_clean_urls(
        self, expected: str, new_temporary_app: App, resource: str
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.clean_urls = True
            async with project:
                sut = LocalizedPathUrlGenerator(project)
                assert sut.generate(resource, "text/html") == expected

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            ("https://example.com", "/"),
            ("https://example.com/example", "example"),
        ],
    )
    async def test_generate_absolute(
        self, expected: str, new_temporary_app: App, resource: str
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = LocalizedPathUrlGenerator(project)
            assert sut.generate(resource, "text/html", absolute=True) == expected

    @pytest.mark.parametrize(
        ("expected", "url_generator_locale"),
        [
            ("/en/index.html", None),
            ("/nl/index.html", "nl"),
            ("/en/index.html", "en"),
        ],
    )
    async def test_generate_multilingual(
        self,
        expected: str,
        new_temporary_app: App,
        url_generator_locale: Localey | None,
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.locales.replace(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            )
            async with project:
                sut = LocalizedPathUrlGenerator(project)
                assert (
                    sut.generate(
                        "/index.html", "text/html", locale=url_generator_locale
                    )
                    == expected
                )


class EntityUrlGeneratorTestUrlyEntity(UserFacingEntity, DummyEntity):
    pass


class EntityUrlGeneratorTestNonUrlyEntity(UserFacingEntity, DummyEntity):
    pass


class TestEntityUrlGenerator:
    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = _EntityUrlGenerator(project, EntityUrlGeneratorTestUrlyEntity)
            assert (
                sut.generate(EntityUrlGeneratorTestUrlyEntity("I1"), "text/html")
                == "/entity-url-generator-test-urly-entity/I1/index.html"
            )


class TestProjectUrlGenerator:
    @pytest.mark.parametrize(
        "resource",
        [
            "/index.html",
            Person(id="P1"),
            Event(
                id="E1",
                event_type=Death(),
            ),
            Place(
                id="P1",
                names=[Name("Place 1")],
            ),
            File(
                id="F1",
                path=Path("/tmp"),
            ),
            Source(
                id="S1",
                name="Source 1",
            ),
            Citation(
                id="C1",
                source=Source("Source 1"),
            ),
        ],
    )
    async def test_supports(self, new_temporary_app: App, resource: Any) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectUrlGenerator(project)
            assert sut.supports(resource)

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            ("/index.html", "/index.html"),
            ("/person/P1/index.html", Person(id="P1")),
            (
                "/event/E1/index.html",
                Event(
                    id="E1",
                    event_type=Death(),
                ),
            ),
            (
                "/place/P1/index.html",
                Place(
                    id="P1",
                    names=[Name("Place 1")],
                ),
            ),
            (
                "/file/F1/index.html",
                File(
                    id="F1",
                    path=Path("/tmp"),
                ),
            ),
            (
                "/source/S1/index.html",
                Source(
                    id="S1",
                    name="Source 1",
                ),
            ),
            (
                "/citation/C1/index.html",
                Citation(
                    id="C1",
                    source=Source("Source 1"),
                ),
            ),
        ],
    )
    async def test_generate(
        self, expected: str, new_temporary_app: App, resource: Any
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectUrlGenerator(project)
            assert sut.generate(resource, "text/html") == expected
