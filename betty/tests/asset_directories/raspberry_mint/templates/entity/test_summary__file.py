from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.file import File
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    file = File(__file__)
    async with assert_template_file(
        data={
            "entity": file,
        },
        assets={raspberry_mint},
        template="entity/summary--file.html.j2",
    ) as (actual, _):
        assert actual
