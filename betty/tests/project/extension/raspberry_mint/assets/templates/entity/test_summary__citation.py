from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/summary--citation.html.j2"

    async def test_minimal(self) -> None:
        source = Source()
        citation = Citation(source=source)
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert source.id in actual

    async def test_with_private_source(self) -> None:
        source = Source(private=True)
        citation = Citation(source=source)
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert source.id not in actual
