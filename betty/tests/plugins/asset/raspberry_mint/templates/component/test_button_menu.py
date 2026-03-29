from betty.html.attributes import Attributes
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        service_plugins={RaspberryMint},
        template="component/button-menu.html.j2",
    ) as (actual, _):
        assert "<button " in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes(html_id=html_id),
        },
        service_plugins={RaspberryMint},
        template="component/button-menu.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
