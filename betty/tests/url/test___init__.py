from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from babel import Locale

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, LocaleLike
from betty.media_type.media_types import HTML
from betty.url import PassthroughUrlGenerator, generate_from_path

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class TestPassthroughUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "wwwexamplecom"),
            (False, "www.example.com"),
            (False, "http://["),
            (True, "http://www.example.com"),
            (True, "https://www.example.com"),
            (True, "some-scheme://www.example.com"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        sut = PassthroughUrlGenerator()
        assert sut.supports(resource) == expected

    async def test_generate(self) -> None:
        resource = "some-scheme://www.example.com"
        sut = PassthroughUrlGenerator()
        assert sut.generate(resource, media_type=HTML) == resource


@pytest.mark.parametrize(
    (
        "expected",
        "root_path",
        "locales",
        "clean_urls",
        "path",
        "absolute",
        "locale",
        "fragment",
        "query",
    ),
    [
        # The simplest and shortest URLs, and the most disabled configuration possible.
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG},
                False,
                path,
                False,
                None,
                None,
                None,
            )
            for expected, path in [
                ("/", "/"),
                ("/index.html", "/index.html"),
                ("/example", "/example"),
                ("/example", "/example/"),
                ("/example/index.html", "/example/index.html"),
            ]
        ],
        # Absolute URLs.
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG},
                False,
                path,
                True,
                None,
                None,
                None,
            )
            for expected, path in [
                ("https://example.com", "/"),
                ("https://example.com/index.html", "/index.html"),
                ("https://example.com/example", "/example"),
                ("https://example.com/example", "/example/"),
                ("https://example.com/example/index.html", "/example/index.html"),
            ]
        ],
        # Clean URLs.
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG},
                True,
                path,
                False,
                None,
                None,
                None,
            )
            for expected, path in [
                ("/", "/"),
                ("/", "/index.html"),
                ("/example", "/example"),
                ("/example", "/example/"),
                ("/example", "/example/index.html"),
            ]
        ],
        # Explicit URL locale.
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG, Locale("nl", "NL"): "nl"},
                False,
                path,
                False,
                "nl-NL",
                None,
                None,
            )
            for expected, path in [
                ("/nl", "/"),
                ("/nl/index.html", "/index.html"),
                ("/nl/example", "/example"),
                ("/nl/example", "/example/"),
                ("/nl/example/index.html", "/example/index.html"),
            ]
        ],
        # Fragments
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG},
                False,
                path,
                False,
                None,
                "my-first-fragment",
                None,
            )
            for expected, path in [
                ("/#my-first-fragment", "/"),
                ("/index.html#my-first-fragment", "/index.html"),
                ("/example#my-first-fragment", "/example"),
                ("/example#my-first-fragment", "/example/"),
                ("/example/index.html#my-first-fragment", "/example/index.html"),
            ]
        ],
        # Queries.
        *[
            (
                expected,
                "/",
                {DEFAULT_LOCALE: DEFAULT_LOCALE_TAG},
                False,
                path,
                False,
                None,
                None,
                {"my_first_query": "my first value"},
            )
            for expected, path in [
                ("/?my_first_query=my+first+value", "/"),
                ("/index.html?my_first_query=my+first+value", "/index.html"),
                ("/example?my_first_query=my+first+value", "/example"),
                ("/example?my_first_query=my+first+value", "/example/"),
                (
                    "/example/index.html?my_first_query=my+first+value",
                    "/example/index.html",
                ),
            ]
        ],
    ],
)
async def test_generate_from_path(
    expected: str,
    root_path: str,
    locales: Mapping[Locale, str],
    clean_urls: bool,
    path: str,
    absolute: bool,
    locale: LocaleLike | None,
    fragment: str | None,
    query: Mapping[str, Sequence[str]] | None,
) -> None:
    assert (
        generate_from_path(
            path,
            absolute=absolute,
            base_url="https://example.com",
            fragment=fragment,
            locale=locale,
            query=query,
            root_path=root_path,
            locale_slugs=locales,
            clean_urls=clean_urls,
        )
        == expected
    )
