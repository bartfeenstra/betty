from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/private.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file():
            pass
