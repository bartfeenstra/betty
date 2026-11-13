from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    label = "Hit me, I am a button!"
    async with assert_raspberry_mint_jinja_file(
        "component/button.html.j2", data={"button_label": label}
    ) as rendered:
        assert "<button " in rendered
        assert "button-primary" in rendered
        assert label in rendered


async def test_secondary(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/button.html.j2",
        data={"button_label": "Hit me, I am a button!", "button_secondary": True},
    ) as rendered:
        assert "button-secondary" in rendered


async def test_with_html_attribute(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/button.html.j2",
        data={
            "button_label": "Hit me, I am a button!",
            "attributes": Attributes(html_id=html_id),
        },
    ) as rendered:
        assert f'id="{html_id}"' in rendered
