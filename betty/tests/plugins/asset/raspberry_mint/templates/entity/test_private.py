from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        assets={RASPBERRY_MINT}, template="entity/private.html.j2"
    ):
        pass
