from betty.renderers.plain_text import PlainText


class TestPlainText:
    async def test_render(self) -> None:
        assert (
            await PlainText().render("Hello...\n~!@#$%^&*()_+\n...world!")
            == "<p>Hello...<br>\n~!@#$%^&amp;*()_+<br>\n...world!</p>"
        )
