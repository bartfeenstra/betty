from betty.html.attributes import Attributes
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    label = "Check me out!"
    value = "Look at this treasure"
    async with assert_template_file(
        data={
            "checkbox_label": label,
            "checkbox_value": value,
        },
        extensions={RaspberryMint},
        template="component/checkbox.html.j2",
    ) as (actual, _):
        assert "<input" in actual
        assert 'type="checkbox"' in actual
        assert label in actual
        assert value in actual


async def test_with_html_attributes() -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "checkbox_label": "Check me out!",
            "attributes": Attributes(html_id=html_id),
        },
        extensions={RaspberryMint},
        template="component/checkbox.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
