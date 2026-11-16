from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    label = "Check these out!"
    async with assert_raspberry_mint_jinja_file(
        "component/checkboxes.html.j2",
        data={
            "checkboxes": [],
            "checkboxes_label": label,
        },
    ) as rendered:
        assert label in rendered


async def test_with_checkboxes_label_visually_hidden(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/checkboxes.html.j2",
        data={
            "checkboxes": [],
            "checkboxes_label": "Check these out!",
            "checkboxes_label_visually_hidden": True,
        },
    ) as rendered:
        assert "visually-hidden" in rendered


async def test_with_minimal_items(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    label = "Check me out!"
    value = "Look at this treasure"
    async with assert_raspberry_mint_jinja_file(
        "component/checkboxes.html.j2",
        data={
            "checkboxes": [
                {
                    "label": label,
                    "value": value,
                }
            ],
            "checkboxes_label": "Check these out!",
        },
    ) as rendered:
        assert label in rendered


async def test_with_full_items(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    html_id = "my-first-id"
    async with assert_raspberry_mint_jinja_file(
        "component/checkboxes.html.j2",
        data={
            "checkboxes": [
                {
                    "label": "Check me out!",
                    "value": "Look at this treasure",
                    "attributes": Attributes(html_id=html_id),
                }
            ],
            "checkboxes_label": "Check these out!",
        },
    ) as rendered:
        assert f'id="{html_id}"' in rendered
