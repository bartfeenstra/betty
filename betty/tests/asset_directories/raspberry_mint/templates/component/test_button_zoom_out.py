from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        assets={RASPBERRY_MINT},
        template="component/button-zoom-out.html.j2",
    ) as (actual, _):
        assert "<button " in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes(html_id=html_id),
        },
        assets={RASPBERRY_MINT},
        template="component/button-zoom-out.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
