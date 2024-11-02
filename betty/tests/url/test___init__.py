from __future__ import annotations


import pytest

from betty.locale import DEFAULT_LOCALE, Localey
from betty.url import generate_from_path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class TestGenerateFromPath:
    @pytest.mark.parametrize(
        (
            "expected",
            "root_path",
            "locales",
            "clean_urls",
            "path",
            "absolute",
            "locale",
        ),
        [
            # The simplest and shortest URLs, and the most disabled configuration possible.
            *[
                (
                    expected,
                    "/",
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    False,
                    path,
                    False,
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
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    False,
                    path,
                    True,
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
                    {DEFAULT_LOCALE: DEFAULT_LOCALE},
                    True,
                    path,
                    False,
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
                    {DEFAULT_LOCALE: DEFAULT_LOCALE, "nl-NL": "nl"},
                    False,
                    path,
                    False,
                    "nl-NL",
                )
                for expected, path in [
                    ("/nl", "/"),
                    ("/nl/index.html", "/index.html"),
                    ("/nl/example", "/example"),
                    ("/nl/example", "/example/"),
                    ("/nl/example/index.html", "/example/index.html"),
                ]
            ],
        ],
    )
    async def test(
        self,
        expected: str,
        root_path: str,
        locales: Mapping[str, str],
        clean_urls: bool,
        path: str,
        absolute: bool,
        locale: Localey | None,
    ) -> None:
        assert (
            generate_from_path(
                path,
                absolute=absolute,
                locale=locale,
                base_url="https://example.com",
                root_path=root_path,
                locales=locales,
                clean_urls=clean_urls,
            )
            == expected
        )
