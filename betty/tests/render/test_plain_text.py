import pytest
from typing_extensions import override

from betty.render import Renderer
from betty.render.plain_text import PlainText
from betty.test_utils.render import RendererTestBase


class TestPlainText(RendererTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Renderer:
        return PlainText()

    async def test_media_type(self) -> None:
        PlainText().media_type  # noqa B018

    async def test_render(self) -> None:
        assert (
            await PlainText().render("Hello...\n~!@#$%^&*()_+\n...world!")
            == "<p>Hello...<br>\n~!@#$%^&amp;*()_+<br>\n...world!</p>"
        )
