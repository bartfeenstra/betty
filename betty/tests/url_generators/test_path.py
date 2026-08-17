from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from babel import Locale

from betty.collections import _empty_frozen_mapping
from betty.locale import ResolvableLocale, default_locale, default_locale_tag
from betty.url_generators.path import PathUrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class TestPathUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (True, "/"),
            (True, "/foo"),
            (True, "/foo/bar"),
            (True, "/foo/bar/"),
            (False, ""),
            (False, "foo"),
            (False, object()),
        ],
    )
    def test_supports(self, expected: bool, resource: Any) -> None:
        sut = PathUrlGenerator(
            base_url="https://example.com",
            root_path="/",
            locales_to_slugs={
                default_locale: default_locale_tag,
            },
            clean_urls=True,
        )
        assert sut.supports(resource) is expected

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
                    {default_locale: default_locale_tag},
                    False,
                    path,
                    False,
                    None,
                    None,
                    _empty_frozen_mapping,
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
                    {default_locale: default_locale_tag},
                    False,
                    path,
                    True,
                    None,
                    None,
                    _empty_frozen_mapping,
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
                    {default_locale: default_locale_tag},
                    True,
                    path,
                    False,
                    None,
                    None,
                    _empty_frozen_mapping,
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
                    {default_locale: default_locale_tag, Locale("nl", "NL"): "nl"},
                    False,
                    path,
                    False,
                    "nl-NL",
                    None,
                    _empty_frozen_mapping,
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
                    {default_locale: default_locale_tag},
                    False,
                    path,
                    False,
                    None,
                    "my-first-fragment",
                    _empty_frozen_mapping,
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
                    {default_locale: default_locale_tag},
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
    async def test_generate(
        self,
        expected: str,
        root_path: str,
        locales: Mapping[Locale, str],
        clean_urls: bool,
        path: str,
        absolute: bool,
        locale: ResolvableLocale | None,
        fragment: str | None,
        query: Mapping[str, Sequence[str]],
    ) -> None:
        sut = PathUrlGenerator(
            base_url="https://example.com",
            root_path=root_path,
            locales_to_slugs=locales,
            clean_urls=clean_urls,
        )
        assert (
            sut.generate(
                path, absolute=absolute, fragment=fragment, locale=locale, query=query
            )
            == expected
        )
