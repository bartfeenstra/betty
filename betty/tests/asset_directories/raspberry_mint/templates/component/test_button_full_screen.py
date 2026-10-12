from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    button_full_screen_target = "#my-first-target"
    async with assert_raspberry_mint_jinja_file(
        "component/button-full-screen.html.j2",
        data={"button_full_screen_target": button_full_screen_target},
    ) as rendered:
        assert "<button " in rendered
        assert button_full_screen_target in rendered


async def test_with_html_attribute(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/button-full-screen.html.j2",
        data={
            "attributes": Attributes(html_id=html_id),
            "button_full_screen_target": "#my-first-target",
        },
    ) as rendered:
        assert f'id="{html_id}"' in rendered
