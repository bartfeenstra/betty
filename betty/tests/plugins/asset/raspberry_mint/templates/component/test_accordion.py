from markupsafe import Markup

from betty.html.attributes import Attributes
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "accordion_items": [],
        },
        assets={RaspberryMint},
        template="component/accordion.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_items(assert_template_file: AssertTemplateFile) -> None:
    accordion_heading_element = "h2"
    header = "Hello, world!"
    body = "<p>Lorem ipsum dolor sit amet</p>"
    async with assert_template_file(
        data={
            "accordion_heading_element": accordion_heading_element,
            "accordion_items": [
                {
                    "header": header,
                    "body": Markup(body),
                },
            ],
        },
        assets={RaspberryMint},
        template="component/accordion.html.j2",
    ) as (actual, _):
        assert f"<{accordion_heading_element}" in actual
        assert header in actual
        assert body in actual


async def test_with_html_attributes(assert_template_file: AssertTemplateFile) -> None:
    html_class = "my-first-class"
    async with assert_template_file(
        data={
            "accordion_heading_element": "h2",
            "accordion_items": [
                {
                    "header": "Hello, world!",
                    "body": Markup("<p>Lorem ipsum dolor sit amet</p>"),
                },
            ],
            "attributes": Attributes(html_class=[html_class]),
        },
        assets={RaspberryMint},
        template="component/accordion.html.j2",
    ) as (actual, _):
        assert html_class in actual
