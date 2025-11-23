from typing import ClassVar

import pytest
from typing_extensions import override

from betty.media_type import MediaType
from betty.media_type.media_types import HTML
from betty.plugin import PluginDefinition
from betty.render import RenderDispatcher, Renderer, RendererDefinition
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase


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
    def media_type(self) -> MediaType:
        return self.MEDIA_TYPE

    @override
    async def render(self, content: str, /) -> str:
        return self.RENDERED_CONTENT


class _StaticRendererOne(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.one", extensions=[".one"])
    RENDERED_CONTENT = "ONE"


class _StaticRendererTwo(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.two", extensions=[".two"])
    RENDERED_CONTENT = "TWO"


class TestRenderDispatcher:
    async def test_render__without_renderers(self) -> None:
        sut = RenderDispatcher()
        assert await sut.render("<html>", HTML) == "<p>&amp;lt;html&amp;gt;</p>"

    async def test_render__with_renderers(self) -> None:
        media_type = MediaType("text/x.betty.test")

        class _Renderer(Renderer):
            @override
            @property
            def media_type(self) -> MediaType:
                return media_type

            @override
            async def render(self, content: str, /) -> str:
                return "~!@#$%^&*()_+"

        sut = RenderDispatcher(_Renderer())
        assert await sut.render("", media_type) == "~!@#$%^&*()_+"
