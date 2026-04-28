from betty.html.attributes import Attributes
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    label = "Hit me, I am a button!"
    async with assert_template_file(
        data={
            "button_label": label,
        },
        assets={RASPBERRY_MINT},
        template="component/button.html.j2",
    ) as (actual, _):
        assert "<button " in actual
        assert "button-primary" in actual
        assert label in actual


async def test_secondary(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "button_secondary": True,
        },
        assets={RASPBERRY_MINT},
        template="component/button.html.j2",
    ) as (actual, _):
        assert "button-secondary" in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "attributes": Attributes(html_id=html_id),
        },
        assets={RASPBERRY_MINT},
        template="component/button.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
