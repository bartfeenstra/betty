from markupsafe import Markup

from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/accordion.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "accordion_items": [],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_items(self) -> None:
        accordion_heading_element = "h2"
        header = "Hello, world!"
        body = "<p>Lorem ipsum dolor sit amet</p>"
        async with self.assert_template_file(
            data={
                "accordion_heading_element": accordion_heading_element,
                "accordion_items": [
                    {
                        "header": header,
                        "body": Markup(body),
                    },
                ],
            }
        ) as (actual, _):
            assert f"<{accordion_heading_element}" in actual
            assert header in actual
            assert body in actual

    async def test_with_html_class(self) -> None:
        html_class = "my-first-class"
        async with self.assert_template_file(
            data={
                "accordion_heading_element": "h2",
                "accordion_items": [
                    {
                        "header": "Hello, world!",
                        "body": Markup("<p>Lorem ipsum dolor sit amet</p>"),
                    },
                ],
                "html_class": [html_class],
            }
        ) as (actual, _):
            assert html_class in actual
