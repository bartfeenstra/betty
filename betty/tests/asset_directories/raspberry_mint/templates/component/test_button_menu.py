from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/button-menu.html.j2"
    ) as rendered:
        assert "<button " in rendered


async def test_with_html_attribute(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/button-menu.html.j2",
        data={"attributes": Attributes(html_id=html_id)},
    ) as rendered:
        assert f'id="{html_id}"' in rendered
