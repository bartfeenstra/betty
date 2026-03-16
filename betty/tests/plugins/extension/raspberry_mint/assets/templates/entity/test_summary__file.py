from pathlib import Path

from betty.ancestry.file import File
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    file = File(Path(__file__))
    async with assert_template_file(
        data={
            "entity": file,
        },
        extensions={RaspberryMint},
        template="entity/summary--file.html.j2",
    ) as (actual, _):
        assert actual
