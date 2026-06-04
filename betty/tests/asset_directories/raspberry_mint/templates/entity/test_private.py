from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        assets={raspberry_mint}, template="entity/private.html.j2"
    ):
        pass
