from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    label = "Check me out!"
    value = "Look at this treasure"
    async with assert_raspberry_mint_jinja_file(
        "component/checkbox.html.j2",
        data={
            "checkbox_label": label,
            "checkbox_value": value,
        },
    ) as rendered:
        assert "<input" in rendered
        assert 'type="checkbox"' in rendered
        assert label in rendered
        assert value in rendered


async def test_with_html_attributes(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/checkbox.html.j2",
        data={
            "checkbox_label": "Check me out!",
            "checkbox_value": "Look at this treasure",
            "attributes": Attributes(html_id=html_id),
        },
    ) as rendered:
        assert f'id="{html_id}"' in rendered
