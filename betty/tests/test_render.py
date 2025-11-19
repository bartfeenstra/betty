from collections.abc import Sequence
from typing import ClassVar

import pytest
from typing_extensions import override

from betty.functools import unique
from betty.media_type import MediaType, UnsupportedMediaType
from betty.plugin import PluginDefinition
from betty.render import ProxyRenderer, Renderer, RendererDefinition
from betty.resource import Context
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestRendererDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return RendererDefinition


class _StaticRenderer(Renderer):
    MEDIA_TYPE: ClassVar[MediaType]
    RENDERED_CONTENT: ClassVar[str]

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return [self.MEDIA_TYPE]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        resource: Context | None = None,
    ) -> str:
        return self.RENDERED_CONTENT


class _StaticRendererOne(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.one", extensions=[".one"])
    RENDERED_CONTENT = "ONE"


class _StaticRendererTwo(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.two", extensions=[".two"])
    RENDERED_CONTENT = "TWO"


class TestProxyRenderer:
    def test_media_types__without_upstreams(self) -> None:
        sut = ProxyRenderer([])
        assert sut.media_types == []

    def test_media_types__with_upstreams(self) -> None:
        renderer_one = _StaticRendererOne()
        renderer_two = _StaticRendererTwo()
        sut = ProxyRenderer([renderer_one, renderer_two])
        assert sut.media_types == list(
            unique(renderer_one.media_types, renderer_two.media_types)
        )

    async def test_render__without_upstreams(self) -> None:
        sut = ProxyRenderer([])
        with pytest.raises(UnsupportedMediaType):
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)

    async def test_render__without_matching_upstream(self) -> None:
        sut = ProxyRenderer([_StaticRendererTwo()])
        with pytest.raises(UnsupportedMediaType):
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)

    async def test_render__with_upstream(self) -> None:
        sut = ProxyRenderer([_StaticRendererOne()])
        assert (
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)
            == _StaticRendererOne.RENDERED_CONTENT
        )
