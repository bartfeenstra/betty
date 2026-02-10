from betty.extension.raspberry_mint import RaspberryMint
from betty.html.attributes import Attributes
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    label = "Hit me, I am a button!"
    async with assert_template_file(
        data={
            "button_label": label,
        },
        extensions={RaspberryMint},
        template="component/button.html.j2",
    ) as (actual, _):
        assert "<button " in actual
        assert "button-primary" in actual
        assert label in actual


async def test_secondary() -> None:
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "button_secondary": True,
        },
        extensions={RaspberryMint},
        template="component/button.html.j2",
    ) as (actual, _):
        assert "button-secondary" in actual


async def test_with_html_attribute() -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "attributes": Attributes(html_id=html_id),
        },
        extensions={RaspberryMint},
        template="component/button.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
