from betty.plugins.renderer.plain_text import PlainText


class TestPlainText:
    async def test_media_type(self) -> None:
        PlainText().media_type  # noqa: B018

    async def test_render(self) -> None:
        assert (
            await PlainText().render("Hello...\n~!@#$%^&*()_+\n...world!")
            == "<p>Hello...<br>\n~!@#$%^&amp;*()_+<br>\n...world!</p>"
        )
