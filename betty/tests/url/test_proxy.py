from collections.abc import Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.locale import Localey
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, JSON
from betty.url import UnsupportedResource, UrlGenerator
from betty.url.proxy import ProxyUrlGenerator


class TestProxyUrlGenerator:
    class _SupportedUrlGenerator(UrlGenerator):
        @override
        def supports(self, resource: Any) -> bool:
            return True

        @override
        def generate(
            self,
            resource: Any,
            *,
            media_type: MediaType | None = None,
            absolute: bool = False,
            locale: Localey | None = None,
        ) -> str:
            return f"{resource}\n{media_type}\n{absolute}\n{locale}"

    class _UnsupportedUrlGenerator(UrlGenerator):
        @override
        def supports(self, resource: Any) -> bool:
            return False

        @override
        def generate(
            self,
            resource: Any,
            *,
            media_type: MediaType | None = None,
            absolute: bool = False,
            locale: Localey | None = None,
        ) -> str:
            raise UnsupportedResource.new(resource)  # pragma: nocover

    @pytest.mark.parametrize(
        ("expected", "upstreams", "resource"),
        [
            (False, [], "/"),
            (False, [_UnsupportedUrlGenerator()], "/"),
            (True, [_SupportedUrlGenerator()], "/"),
            (
                True,
                [
                    _UnsupportedUrlGenerator(),
                    _SupportedUrlGenerator(),
                ],
                "/",
            ),
        ],
    )
    async def test_supports(
        self, expected: bool, resource: Any, upstreams: Sequence[UrlGenerator]
    ) -> None:
        sut = ProxyUrlGenerator(*upstreams)
        assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        ("expected", "resource", "media_type", "absolute", "locale"),
        [
            (
                "/\ntext/html\nFalse\nNone",
                "/",
                HTML,
                False,
                None,
            ),
            (
                "/\napplication/json\nFalse\nNone",
                "/",
                JSON,
                False,
                None,
            ),
            (
                "/\ntext/html\nTrue\nNone",
                "/",
                HTML,
                True,
                None,
            ),
            (
                "/\ntext/html\nFalse\nnl-NL",
                "/",
                HTML,
                False,
                "nl-NL",
            ),
        ],
    )
    async def test_generate(
        self,
        expected: str,
        resource: Any,
        media_type: MediaType,
        absolute: bool,
        locale: Localey | None,
    ) -> None:
        sut = ProxyUrlGenerator(
            self._UnsupportedUrlGenerator(),
            self._SupportedUrlGenerator(),
        )
        assert (
            sut.generate(
                resource, media_type=media_type, absolute=absolute, locale=locale
            )
            == expected
        )
