from betty.extension.raspberry_mint import RaspberryMint
from betty.html.attributes import Attributes
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        extensions={RaspberryMint},
        template="component/button-close.html.j2",
    ) as (actual, _):
        assert "<button " in actual


async def test_with_html_attribute() -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes(html_id=html_id),
        },
        extensions={RaspberryMint},
        template="component/button-close.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
