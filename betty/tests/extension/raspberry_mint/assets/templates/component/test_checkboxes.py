from betty.extension.raspberry_mint import RaspberryMint
from betty.html.attributes import Attributes
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    label = "Check these out!"
    async with assert_template_file(
        data={
            "checkboxes": [],
            "checkboxes_label": label,
        },
        extensions={RaspberryMint},
        template="component/checkboxes.html.j2",
    ) as (actual, _):
        assert label in actual


async def test_with_checkboxes_label_visually_hidden() -> None:
    async with assert_template_file(
        data={
            "checkboxes": [],
            "checkboxes_label": "Check these out!",
            "checkboxes_label_visually_hidden": True,
        },
        extensions={RaspberryMint},
        template="component/checkboxes.html.j2",
    ) as (actual, _):
        assert "visually-hidden" in actual


async def test_with_minimal_items() -> None:
    label = "Check me out!"
    value = "Look at this treasure"
    async with assert_template_file(
        data={
            "checkboxes": [
                {
                    "label": label,
                    "value": value,
                }
            ],
            "checkboxes_label": "Check these out!",
        },
        extensions={RaspberryMint},
        template="component/checkboxes.html.j2",
    ) as (actual, _):
        assert label in actual


async def test_with_full_items() -> None:
    html_id = "my-first-id"
    async with assert_template_file(
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
        extensions={RaspberryMint},
        template="component/checkboxes.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
