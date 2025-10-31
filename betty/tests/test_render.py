from collections.abc import Sequence
from pathlib import Path

import pytest
from typing_extensions import override

from betty.functools import unique
from betty.job import Context
from betty.locale.localizer import Localizer
from betty.media_type import MediaType
from betty.plugin import PluginDefinition
from betty.render import Renderer, RendererDefinition, SequentialRenderer
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestRendererDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return RendererDefinition


class _Renderer(Renderer):
    _media_types: Sequence[MediaType]
    _render_file_path: Path

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return self._media_types

    @override
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        return self._render_file_path


class _RendererOne(_Renderer):
    _media_types = [MediaType("text/x.betty.test.one", extensions=[".one"])]
    _render_file_path = Path("one.html")


class _RendererTwo(_Renderer):
    _media_types = [MediaType("text/x.betty.test.two", extensions=[".two"])]
    _render_file_path = Path("two.html")


class TestSequentialRenderer:
    def test_media_types__without_upstreams(self) -> None:
        sut = SequentialRenderer([])
        assert sut.media_types == []

    def test_media_types__with_upstreams(self) -> None:
        renderer_one = _RendererOne()
        renderer_two = _RendererTwo()
        sut = SequentialRenderer([renderer_one, renderer_two])
        assert sut.media_types == list(
            unique(renderer_one.media_types, renderer_two.media_types)
        )

    async def test_render_file__without_upstreams(self) -> None:
        sut = SequentialRenderer([])
        await sut.render_file(Path())

    async def test_render_file__without_matching_upstream(self) -> None:
        sut = SequentialRenderer([_RendererTwo()])
        await sut.render_file(Path("something.one"))

    async def test_render_file__with_upstream(self) -> None:
        sut = SequentialRenderer([_RendererOne()])
        assert await sut.render_file(Path("something.one")) == Path("one.html")
