from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        extensions={RaspberryMint}, template="entity/private.html.j2"
    ):
        pass
