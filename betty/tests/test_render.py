from typing import override

from betty.content_type import ContentTypeDefinition
from betty.content_types import html
from betty.render import RenderDispatcher, Renderer


class TestRenderDispatcher:
    async def test_render__without_renderers(self) -> None:
        sut = RenderDispatcher()
        assert await sut.render("<html>", html) == "<p>&lt;html&gt;</p>"

    async def test_render__with_renderers(self) -> None:
        media_type = ContentTypeDefinition(
            "test", label="-", media_type="text/x.betty.test"
        )

        class _Renderer(Renderer):
            @override
            async def render(self, content: str, /) -> str:
                return "~!@#$%^&*()_+"

        sut = RenderDispatcher(_Renderer())
        assert await sut.render("", media_type) == "~!@#$%^&*()_+"
