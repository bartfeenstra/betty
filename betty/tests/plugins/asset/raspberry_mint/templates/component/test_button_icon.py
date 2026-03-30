from betty.html.attributes import Attributes
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    label = "Hit me, I am a button!"
    async with assert_template_file(
        data={
            "button_label": label,
        },
        assets={RaspberryMint},
        template="component/button-icon.html.j2",
    ) as (actual, _):
        assert "<button " in actual
        assert label in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes(html_id=html_id),
        },
        assets={RaspberryMint},
        template="component/button-icon.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
