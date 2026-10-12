from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    label = "Hit me, I am a button!"
    async with assert_raspberry_mint_jinja_file(
        "component/button-icon.html.j2", data={"button_label": label}
    ) as rendered:
        assert "<button " in rendered
        assert label in rendered


async def test_with_html_attribute(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/button-icon.html.j2",
        data={
            "attributes": Attributes(html_id=html_id),
            "button_label": "Hit me, I am a button!",
        },
    ) as rendered:
        assert f'id="{html_id}"' in rendered
