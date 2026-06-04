from typing import ClassVar, override

from betty.media_type import MediaType
from betty.media_types.html import HTML
from betty.render import RenderDispatcher, Renderer


class _StaticRenderer(Renderer):
    _media_type: ClassVar[MediaType]
    _rendered_content: ClassVar[str]

    @override
    @property
    def media_type(self) -> MediaType:
        return self._media_type

    @override
    async def render(self, content: str, /) -> str:
        return self._rendered_content


class _StaticRendererOne(_StaticRenderer):
    _media_type: ClassVar[MediaType] = MediaType(
        "text/x.betty.test.one", extensions=[".one"]
    )
    _rendered_content: ClassVar[str] = "ONE"


class _StaticRendererTwo(_StaticRenderer):
    _media_type: ClassVar[MediaType] = MediaType(
        "text/x.betty.test.two", extensions=[".two"]
    )
    _rendered_content: ClassVar[str] = "TWO"


class TestRenderDispatcher:
    async def test_render__without_renderers(self) -> None:
        sut = RenderDispatcher()
        assert await sut.render("<html>", HTML) == "<p>&lt;html&gt;</p>"

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
