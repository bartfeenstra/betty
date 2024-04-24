from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from betty.app import App
from betty.locale import Localey
from betty.model import UserFacingEntity, Entity
from betty.model.ancestry import Person, Place, File, Source, PlaceName, Event, Citation
from betty.model.event_type import Death
from betty.project import LocaleConfiguration
from betty.url import LocalizedPathUrlGenerator, _EntityUrlGenerator, AppUrlGenerator


class TestLocalizedPathUrlGenerator:
    @pytest.mark.parametrize(
        "expected, resource",
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
    async def test_generate(self, expected: str, resource: str) -> None:
        async with App.new_temporary() as app, app:
            sut = LocalizedPathUrlGenerator(app)
            assert expected == sut.generate(resource, "text/html")

    @pytest.mark.parametrize(
        "expected, resource",
        [
            ("", "index.html"),
            ("", "/index.html"),
            ("/example", "example/index.html"),
            ("/example", "/example/index.html"),
        ],
    )
    async def test_generate_with_clean_urls(self, expected: str, resource: str) -> None:
        async with App.new_temporary() as app, app:
            app.project.configuration.clean_urls = True
            sut = LocalizedPathUrlGenerator(app)
            assert expected == sut.generate(resource, "text/html")

    @pytest.mark.parametrize(
        "expected, resource",
        [
            ("https://example.com", "/"),
            ("https://example.com/example", "example"),
        ],
    )
    async def test_generate_absolute(self, expected: str, resource: str) -> None:
        async with App.new_temporary() as app, app:
            sut = LocalizedPathUrlGenerator(app)
            assert expected == sut.generate(resource, "text/html", absolute=True)

    @pytest.mark.parametrize(
        "expected, url_generator_locale",
        [
            ("/en/index.html", None),
            ("/nl/index.html", "nl"),
            ("/en/index.html", "en"),
        ],
    )
    async def test_generate_multilingual(
        self,
        expected: str,
        url_generator_locale: Localey | None,
    ) -> None:
        async with App.new_temporary() as app, app:
            app.project.configuration.locales.replace(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            )
            sut = LocalizedPathUrlGenerator(app)
            assert expected == sut.generate(
                "/index.html", "text/html", locale=url_generator_locale
            )


class EntityUrlGeneratorTestUrlyEntity(UserFacingEntity, Entity):
    pass


class EntityUrlGeneratorTestNonUrlyEntity(UserFacingEntity, Entity):
    pass


class TestEntityUrlGenerator:
    async def test_generate(self) -> None:
        async with App.new_temporary() as app, app:
            sut = _EntityUrlGenerator(app, EntityUrlGeneratorTestUrlyEntity)
            assert (
                "/betty.tests.test_url.-entity-url-generator-test-urly-entity/I1/index.html"
                == sut.generate(EntityUrlGeneratorTestUrlyEntity("I1"), "text/html")
            )

    async def test_generate_with_invalid_value(self) -> None:
        async with App.new_temporary() as app, app:
            sut = _EntityUrlGenerator(app, EntityUrlGeneratorTestUrlyEntity)
            with pytest.raises(ValueError):
                sut.generate(EntityUrlGeneratorTestNonUrlyEntity(), "text/html")


class TestAppUrlGenerator:
    @pytest.mark.parametrize(
        "expected, resource",
        [
            ("/index.html", "/index.html"),
            ("/person/P1/index.html", Person(id="P1")),
            (
                "/event/E1/index.html",
                Event(
                    id="E1",
                    event_type=Death,
                ),
            ),
            (
                "/place/P1/index.html",
                Place(
                    id="P1",
                    names=[PlaceName(name="Place 1")],
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
    async def test_generate(self, expected: str, resource: Any) -> None:
        async with App.new_temporary() as app, app:
            sut = AppUrlGenerator(app)
            assert expected == sut.generate(resource, "text/html")
