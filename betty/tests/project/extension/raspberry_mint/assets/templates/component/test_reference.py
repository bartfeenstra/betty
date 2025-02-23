from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/reference.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "citations": [],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_citation(self) -> None:
        async with self.assert_template_file(
            data={
                "citations": [
                    Citation(source=Source()),
                ],
            }
        ) as (actual, _):
            assert actual == ' <sup><a href="#reference-1">[1]</a></sup>'
