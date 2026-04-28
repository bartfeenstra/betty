from pathlib import Path

from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.file import File
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    file = File(Path(__file__))
    async with assert_template_file(
        data={
            "entity": file,
        },
        assets={RASPBERRY_MINT},
        template="entity/summary--file.html.j2",
    ) as (actual, _):
        assert actual
