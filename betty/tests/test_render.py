from typing import override

from betty.media_type import MediaType, MediaTypeDefinition
from betty.media_types import html
from betty.render import RenderDispatcher, Renderer


class TestRenderDispatcher:
    async def test_render__without_renderers(self) -> None:
        sut = RenderDispatcher()
        assert await sut.render("<html>", html) == "<p>&lt;html&gt;</p>"

    async def test_render__with_renderers(self) -> None:
        media_type = MediaType("text/x.betty.test")

        class _Renderer(Renderer):
            @override
            @property
            def media_type(self) -> MediaTypeDefinition:
                return media_type

            @override
            async def render(self, content: str, /) -> str:
                return "~!@#$%^&*()_+"

        sut = RenderDispatcher(_Renderer())
        assert await sut.render("", media_type) == "~!@#$%^&*()_+"
