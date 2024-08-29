from collections.abc import Sequence
from pathlib import Path
from typing import Mapping

import pytest
from typing_extensions import override

from betty.job import Context
from betty.locale.localizer import Localizer
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT, HTML
from betty.render import ProxyRenderer, Renderer, MediaTypeIndicator


class TestRenderer:
    @pytest.mark.parametrize(
        ("expected", "media_type_indicator", "media_types"),
        [
            ((PLAIN_TEXT, PLAIN_TEXT), "betty.txt", [PLAIN_TEXT]),
            (None, "betty", [PLAIN_TEXT]),
            ((PLAIN_TEXT, PLAIN_TEXT), Path("betty.txt"), [PLAIN_TEXT]),
            (None, Path("betty"), [PLAIN_TEXT]),
            ((PLAIN_TEXT, PLAIN_TEXT), PLAIN_TEXT, [PLAIN_TEXT]),
            (None, HTML, [PLAIN_TEXT]),
        ],
    )
    def test_to_media_type(
        self,
        expected: tuple[MediaType, MediaType] | None,
        media_type_indicator: MediaTypeIndicator,
        media_types: Sequence[MediaType],
    ) -> None:
        class _DummyRenderer(Renderer):
            def __init__(self, *media_types: MediaType):
                self._media_types = {
                    media_type: media_type for media_type in media_types
                }

            @override
            @property
            def media_types(self) -> Mapping[MediaType, MediaType]:
                return self._media_types

            @override
            async def render(
                self,
                content: str,
                media_type_indicator: MediaTypeIndicator,
                *,
                job_context: Context | None = None,
                localizer: Localizer | None = None,
            ) -> tuple[str, MediaType, MediaType]:
                from_media_type, to_media_type = self.assert_to_media_type(
                    media_type_indicator
                )
                return content, from_media_type, to_media_type

        assert (
            _DummyRenderer(*media_types).to_media_type(media_type_indicator) == expected
        )

    def test_copy_function(self) -> None:
        raise AssertionError


class DummyRenderer(Renderer):
    @override
    @property
    def media_types(self) -> Mapping[MediaType, MediaType]:
        return {PLAIN_TEXT: PLAIN_TEXT}

    @override
    async def render(
        self,
        content: str,
        media_type_indicator: MediaTypeIndicator,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> tuple[str, MediaType, MediaType]:
        return content, PLAIN_TEXT, PLAIN_TEXT


class ErroringDummyRenderer(Renderer):
    @override
    @property
    def media_types(self) -> Mapping[MediaType, MediaType]:
        return {PLAIN_TEXT: PLAIN_TEXT}

    @override
    async def render(
        self,
        content: str,
        media_type_indicator: MediaTypeIndicator,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> tuple[str, MediaType, MediaType]:
        raise RuntimeError


class TestProxyRenderer:
    def test_media_types_without_upstreams(self) -> None:
        sut = ProxyRenderer([])
        assert not sut.media_types

    def test_media_types_with_upstreams(self) -> None:
        sut = ProxyRenderer([DummyRenderer()])
        assert sut.media_types

    async def test_render(self) -> None:
        sut = ProxyRenderer([DummyRenderer(), ErroringDummyRenderer()])
        content = "Hello, world!"
        rendered, from_media_type, to_media_type = await sut.render(content, PLAIN_TEXT)
        assert rendered == content
        assert from_media_type is PLAIN_TEXT
        assert to_media_type is PLAIN_TEXT
