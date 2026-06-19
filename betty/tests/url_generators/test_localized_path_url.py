from collections.abc import Sequence
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
from betty.url_generators.localized_path_url import LocalizedPathUrlUrlGenerator
from betty.url_generators.path import PathUrlGenerator


class TestLocalizedPathUrlUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty"),
            (False, "betty://"),
            (False, "betty://["),
            (True, "betty://without-leading-slash/index.html"),
            (True, "betty:///with-leading-slash/index.html"),
            (False, "betty-other://without-leading-slash/index.html"),
            (False, "betty-other:///with-leading-slash/index.html"),
            (False, "/"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        sut = LocalizedPathUrlUrlGenerator(
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

    _GENERATE_RESOURCES: ClassVar[Sequence[str]] = [
        "betty://some/path/index.html",
        "betty:///some/path/index.html",
    ]

    @pytest.mark.parametrize(
        (
            "expected",
            "resource",
            "media_type",
            "absolute",
            "locale",
            "additional_project_locale",
        ),
        [
            *[
                (
                    "/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    None,
                    None,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    "https://example.com/some/path/index.html",
                    resource,
                    media_type,
                    True,
                    None,
                    None,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    f"/{default_locale_tag}/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    None,
                    Locale("nl", "NL"),
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    "/nl-NL/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    "nl-NL",
                    Locale("nl", "NL"),
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
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
    ) -> None:
        project_locales = [default_locale]
        if additional_project_locale:
            project_locales.append(additional_project_locale)
        sut = LocalizedPathUrlUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    project_locale: to_language_tag(project_locale)
                    for project_locale in project_locales
                },
                clean_urls=False,
            )
        )
        assert (
            sut.generate(
                resource,
                media_type=media_type,
                absolute=absolute,
                locale=locale,
            )
            == expected
        )
