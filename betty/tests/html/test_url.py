from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.html.url import generate_urls
from betty.locale import LocaleLike
from betty.media_type import MediaType
from betty.url import UrlGenerator


class _GenerateUrlsUrlGenerator(UrlGenerator):
    @override
    def supports(self, resource: Any, /) -> bool:
        return isinstance(resource, str) and resource == "my-first-resource://"

    @override
    def generate(
        self,
        resource: str,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        return "GENERATED-URL-AHOY"


@pytest.mark.parametrize(
    ("expected", "html"),
    [
        ("", ""),
        (
            '<a href="https://example.com">linked</a>',
            '<a href="https://example.com">linked</a>',
        ),
        (
            'Hello, <a href="https://example.com">linked</a> world!',
            'Hello, <a href="https://example.com">linked</a> world!',
        ),
        (
            '<a href="GENERATED-URL-AHOY" src="my-first-resource://">linked</a>',
            '<a href="my-first-resource://" src="my-first-resource://">linked</a>',
        ),
        (
            'Hello, <a href="GENERATED-URL-AHOY" src="my-first-resource://">linked</a> world!',
            'Hello, <a href="my-first-resource://" src="my-first-resource://">linked</a> world!',
        ),
        (
            'Hello, <a href="GENERATED-URL-AHOY" src="my-first-resource://">linked</a> <em>world</em>!',
            'Hello, <a href="my-first-resource://" src="my-first-resource://">linked</a> <em>world</em>!',
        ),
    ],
)
async def test_generate_urls(expected: str, html: str) -> None:
    assert (
        generate_urls(html, ["href"], url_generator=_GenerateUrlsUrlGenerator())
        == expected
    )
