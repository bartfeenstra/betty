from collections.abc import Mapping
from typing import Any

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.locale import Localey, DEFAULT_LOCALE
from betty.media_type import MediaType
from betty.media_type.media_types import HTML
from betty.model import ENTITY_TYPE_REPOSITORY, Entity
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.project.url import StaticUrlGenerator, LocalizedUrlGenerator
from betty.test_utils.model import DummyEntity


class TestLocalizedUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (True, "/"),
            (True, "/index.html"),
            (True, "/example"),
            (True, "/example/"),
            (True, "/example/index.html"),
            (True, DummyEntity()),
            (False, ""),
            (False, "index.html"),
            (False, "example"),
            (False, "example/"),
            (False, "example/index.html"),
            (False, object()),
        ],
    )
    async def test_supports(
        self,
        expected: bool,
        resource: Any,
        new_temporary_app: App,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=ProxyPluginRepository[Entity](
                StaticPluginRepository(DummyEntity), ENTITY_TYPE_REPOSITORY
            ),
        )
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await LocalizedUrlGenerator.new_for_project(project)
            assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        (
            "expected",
            "url",
            "locales",
            "clean_urls",
            "resource",
            "media_type",
            "absolute",
            "locale",
        ),
        [
            # The simplest and shortest URLs, and the most disabled configuration possible.
            *[
                (
                    expected,
                    "https://example.com/",
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    False,
                    path,
                    HTML,
                    False,
                    None,
                )
                for expected, path in [
                    ("/", "/"),
                    ("/index.html", "/index.html"),
                    ("/example", "/example"),
                    ("/example", "/example/"),
                    ("/example/index.html", "/example/index.html"),
                    (
                        "/dummy-entity/my-first-entity/index.html",
                        DummyEntity(id="my-first-entity"),
                    ),
                ]
            ],
            # Absolute URLs.
            *[
                (
                    expected,
                    "https://example.com/",
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    False,
                    path,
                    HTML,
                    True,
                    None,
                )
                for expected, path in [
                    ("https://example.com", "/"),
                    ("https://example.com/index.html", "/index.html"),
                    ("https://example.com/example", "/example"),
                    ("https://example.com/example", "/example/"),
                    ("https://example.com/example/index.html", "/example/index.html"),
                    (
                        "https://example.com/dummy-entity/my-first-entity/index.html",
                        DummyEntity(id="my-first-entity"),
                    ),
                ]
            ],
            # Clean URLs.
            *[
                (
                    expected,
                    "https://example.com/",
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    True,
                    path,
                    HTML,
                    False,
                    None,
                )
                for expected, path in [
                    ("/", "/"),
                    ("/", "/index.html"),
                    ("/example", "/example"),
                    ("/example", "/example/"),
                    ("/example", "/example/index.html"),
                    (
                        "/dummy-entity/my-first-entity",
                        DummyEntity(id="my-first-entity"),
                    ),
                ]
            ],
        ],
    )
    async def test_generate(
        self,
        expected: str,
        url: str,
        locales: Mapping[str, str],
        clean_urls: bool,
        resource: str,
        media_type: MediaType,
        absolute: bool,
        locale: Localey | None,
        new_temporary_app: App,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=ProxyPluginRepository[Entity](
                StaticPluginRepository(DummyEntity), ENTITY_TYPE_REPOSITORY
            ),
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.url = url
            project.configuration.locales.replace(
                *[
                    LocaleConfiguration(locale, alias=alias)
                    for locale, alias in locales.items()
                ]
            )
            project.configuration.clean_urls = clean_urls
            async with project:
                sut = await LocalizedUrlGenerator.new_for_project(project)
                assert (
                    sut.generate(resource, media_type, absolute=absolute, locale=locale)
                    == expected
                )


class TestStaticUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (True, "/"),
            (True, "/index.html"),
            (True, "/example"),
            (True, "/example/"),
            (True, "/example/index.html"),
            (False, ""),
            (False, "index.html"),
            (False, "example"),
            (False, "example/"),
            (False, "example/index.html"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        sut = StaticUrlGenerator(
            "https://example.com", "/", {DEFAULT_LOCALE: DEFAULT_LOCALE}, False
        )
        assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        (
            "expected",
            "base_url",
            "root_path",
            "locales",
            "clean_urls",
            "resource",
            "absolute",
        ),
        [
            (
                "/index.html",
                "https://example.com",
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE},
                False,
                "/index.html",
                False,
            ),
            # Absolute URLs.
            (
                "https://example.com/index.html",
                "https://example.com",
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE},
                False,
                "/index.html",
                True,
            ),
            # Clean URLs.
            (
                "/",
                "https://example.com",
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE},
                True,
                "/index.html",
                False,
            ),
        ],
    )
    async def test_generate(
        self,
        expected: str,
        base_url: str,
        root_path: str,
        locales: Mapping[str, str],
        clean_urls: bool,
        resource: str,
        absolute: bool,
    ) -> None:
        sut = StaticUrlGenerator(base_url, root_path, locales, clean_urls)
        assert sut.generate(resource, absolute=absolute) == expected
