from pathlib import Path

from betty.ancestry.file import File
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/summary--file.html.j2"

    async def test_minimal(self) -> None:
        file = File(Path(__file__))
        async with self.assert_template_file(
            data={
                "entity": file,
            }
        ) as (actual, _):
            assert actual
