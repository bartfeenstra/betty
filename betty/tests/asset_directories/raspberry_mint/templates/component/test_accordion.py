from markupsafe import Markup

from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/accordion.html.j2", data={"accordion_items": []}
    ) as rendered:
        assert rendered == ""


async def test_with_items(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    accordion_heading_element = "h2"
    header = "Hello, world!"
    body = "<p>Lorem ipsum dolor sit amet</p>"
    async with assert_raspberry_mint_jinja_file(
        "component/accordion.html.j2",
        data={
            "accordion_heading_element": accordion_heading_element,
            "accordion_items": [
                {
                    "header": header,
                    "body": Markup(body),
                },
            ],
        },
    ) as rendered:
        assert f"<{accordion_heading_element}" in rendered
        assert header in rendered
        assert body in rendered


async def test_with_html_attributes(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_class = "my-first-class"
    async with assert_raspberry_mint_jinja_file(
        "component/accordion.html.j2",
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
    ) as rendered:
        assert html_class in rendered
