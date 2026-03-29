from betty.html.attributes import Attributes
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        extensions={RaspberryMint},
        template="component/button-full-screen.html.j2",
    ) as (actual, _):
        assert "<button " in actual


async def test_with_html_attribute(assert_template_file: AssertTemplateFile) -> None:  # noqa: F821
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "attributes": Attributes(html_id=html_id),
        },
        extensions={RaspberryMint},
        template="component/button-full-screen.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual
