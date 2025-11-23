from collections.abc import Mapping, Sequence
from json import dumps, loads
from typing import Any

import pytest
from typing_extensions import override

from betty.locale import LocaleLike
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, JSON
from betty.url import UnsupportedResource, UrlGenerator
from betty.url.proxy import ProxyUrlGenerator


class TestProxyUrlGenerator:
    class _SupportedUrlGenerator(UrlGenerator):
        @override
        def supports(self, resource: Any, /) -> bool:
            return True

        @override
        def generate(
            self,
            resource: Any,
            *,
            absolute: bool = False,
            fragment: str | None = None,
            locale: LocaleLike | None = None,
            media_type: MediaType | None = None,
            query: Mapping[str, Sequence[str]] | None = None,
        ) -> str:
            return dumps(
                {
                    "resource": resource,
                    "media_type": str(media_type),
                    "absolute": absolute,
                    "locale": locale,
                    "fragment": fragment,
                    "query": query,
                }
            )

    class _UnsupportedUrlGenerator(UrlGenerator):
        @override
        def supports(self, resource: Any, /) -> bool:
            return False

        @override
        def generate(
            self,
            resource: Any,
            *,
            absolute: bool = False,
            fragment: str | None = None,
            locale: LocaleLike | None = None,
            media_type: MediaType | None = None,
            query: Mapping[str, Sequence[str]] | None = None,
        ) -> str:
            raise UnsupportedResource(resource)  # pragma: nocover

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
        (
            "resource",
            "media_type",
            "absolute",
            "locale",
            "fragment",
            "query",
        ),
        [
            (
                "/",
                HTML,
                False,
                None,
                None,
                None,
            ),
            (
                "/",
                JSON,
                False,
                None,
                None,
                None,
            ),
            (
                "/",
                HTML,
                True,
                None,
                None,
                None,
            ),
            (
                "/",
                HTML,
                False,
                "nl-NL",
                None,
                None,
            ),
            (
                "/",
                HTML,
                False,
                None,
                "my-first-fragment",
                None,
            ),
            (
                "/",
                HTML,
                False,
                None,
                None,
                {"my_first_query": "my first value"},
            ),
        ],
    )
    async def test_generate(
        self,
        resource: Any,
        media_type: MediaType,
        absolute: bool,
        locale: LocaleLike | None,
        fragment: str | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> None:
        sut = ProxyUrlGenerator(
            self._UnsupportedUrlGenerator(),
            self._SupportedUrlGenerator(),
        )
        assert loads(
            sut.generate(
                resource,
                absolute=absolute,
                fragment=fragment,
                locale=locale,
                media_type=media_type,
                query=query,
            )
        ) == {
            "resource": resource,
            "media_type": str(media_type),
            "absolute": absolute,
            "locale": locale,
            "fragment": fragment,
            "query": query,
        }
