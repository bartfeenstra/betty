from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.html.attributes import Attributes
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        assets={raspberry_mint},
        template="component/button-full-screen.html.j2",
    ) as (actual, _):
        assert "<button " in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes().set(html_id=html_id),
        },
        assets={raspberry_mint},
        template="component/button-full-screen.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
