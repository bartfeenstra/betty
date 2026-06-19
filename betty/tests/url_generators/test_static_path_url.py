from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import pytest
from babel import Locale

from betty.locale import (
    ResolvableLocale,
    default_locale,
    default_locale_tag,
    to_language_tag,
)
from betty.media_type import MediaType
from betty.media_types.html import HTML
from betty.media_types.json import JSON
from betty.url_generators.path import PathUrlGenerator
from betty.url_generators.static_path_url import StaticPathUrlUrlGenerator


class TestStaticPathUrlUrlGenerator:
    _GENERATE_RESOURCES: ClassVar[Sequence[str]] = [
        "betty-static://some/path/index.html",
        "betty-static:///some/path/index.html",
    ]

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty-static"),
            (False, "betty-static://"),
            (False, "betty-static://["),
            (True, "betty-static://without-leading-slash/index.html"),
            (True, "betty-static:///with-leading-slash/index.html"),
            (False, "betty-static-other://without-leading-slash/index.html"),
            (False, "betty-static-other:///with-leading-slash/index.html"),
            (False, "/"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        sut = StaticPathUrlUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    default_locale: default_locale_tag,
                },
                clean_urls=True,
            )
        )
        assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        (
            "expected",
            "resource",
            "media_type",
            "absolute",
            "locale",
            "additional_project_locale",
            "fragment",
            "query",
        ),
        [
            *[
                (
                    "https://example.com/some/path/index.html?my_first_query=my+first+value#my-first-fragment",
                    resource,
                    media_type,
                    True,
                    locale,
                    additional_project_locale,
                    "my-first-fragment",
                    {"my_first_query": "my first value"},
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
                for locale in [None, "nl-NL"]
                for additional_project_locale in [None, Locale("nl", "NL")]
            ],
            *[
                (
                    "/some/path/index.html?my_first_query=my+first+value#my-first-fragment",
                    resource,
                    media_type,
                    False,
                    locale,
                    additional_project_locale,
                    "my-first-fragment",
                    {"my_first_query": "my first value"},
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
                for locale in [None, "nl-NL"]
                for additional_project_locale in [None, Locale("nl", "NL")]
            ],
        ],
    )
    async def test_generate(
        self,
        expected: str,
        resource: str,
        media_type: MediaType,
        absolute: bool,
        locale: ResolvableLocale | None,
        additional_project_locale: Locale | None,
        fragment: str | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> None:
        locales = [default_locale]
        if additional_project_locale:
            locales.append(additional_project_locale)
        sut = StaticPathUrlUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    locale: to_language_tag(locale) for locale in locales
                },
                clean_urls=False,
            )
        )
        assert (
            sut.generate(
                resource,
                absolute=absolute,
                fragment=fragment,
                locale=locale,
                media_type=media_type,
                query=query,
            )
            == expected
        )
