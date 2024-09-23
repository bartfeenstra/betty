from collections.abc import Sequence
from typing import Any
from typing_extensions import override

import pytest

from betty.locale import Localey
from betty.url import LocalizedUrlGenerator, UnsupportedResource
from betty.url.proxy import ProxyLocalizedUrlGenerator


class TestProxyLocalizedUrlGenerator:
    class _SupportedLocalizedUrlGenerator(LocalizedUrlGenerator):
        @override
        def supports(self, resource: Any) -> bool:
            return True

        @override
        def generate(
            self,
            resource: Any,
            media_type: str,
            *,
            absolute: bool = False,
            locale: Localey | None = None,
        ) -> str:
            return f"{resource}\n{media_type}\n{absolute}\n{locale}"

    class _UnsupportedLocalizedUrlGenerator(LocalizedUrlGenerator):
        @override
        def supports(self, resource: Any) -> bool:
            return False

        @override
        def generate(
            self,
            resource: Any,
            media_type: str,
            *,
            absolute: bool = False,
            locale: Localey | None = None,
        ) -> str:
            raise UnsupportedResource.new(resource)

    @pytest.mark.parametrize(
        ("expected", "upstreams", "resource"),
        [
            (False, [], "/"),
            (False, [_UnsupportedLocalizedUrlGenerator()], "/"),
            (True, [_SupportedLocalizedUrlGenerator()], "/"),
            (
                True,
                [
                    _UnsupportedLocalizedUrlGenerator(),
                    _SupportedLocalizedUrlGenerator(),
                ],
                "/",
            ),
        ],
    )
    async def test_supports(
        self, expected: bool, resource: Any, upstreams: Sequence[LocalizedUrlGenerator]
    ) -> None:
        sut = ProxyLocalizedUrlGenerator(*upstreams)
        assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        ("expected", "resource", "media_type", "absolute", "locale"),
        [
            (
                "/\ntext/html\nFalse\nNone",
                "/",
                "text/html",
                False,
                None,
            ),
            (
                "/\napplication/json\nFalse\nNone",
                "/",
                "application/json",
                False,
                None,
            ),
            (
                "/\ntext/html\nTrue\nNone",
                "/",
                "text/html",
                True,
                None,
            ),
            (
                "/\ntext/html\nFalse\nnl-NL",
                "/",
                "text/html",
                False,
                "nl-NL",
            ),
        ],
    )
    async def test_generate(
        self,
        expected: str,
        resource: Any,
        media_type: str,
        absolute: bool,
        locale: Localey | None,
    ) -> None:
        sut = ProxyLocalizedUrlGenerator(
            self._UnsupportedLocalizedUrlGenerator(),
            self._SupportedLocalizedUrlGenerator(),
        )
        assert (
            sut.generate(resource, media_type, absolute=absolute, locale=locale)
            == expected
        )
