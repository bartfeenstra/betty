from betty.ancestry.source import Source
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/summary--source.html.j2"

    async def test_minimal(self) -> None:
        source = Source()
        async with self.assert_template_file(
            data={
                "entity": source,
            }
        ) as (actual, _):
            assert actual

    async def test_with_contained_by(self) -> None:
        contained_by_source = Source()
        source = Source(contained_by=contained_by_source)
        async with self.assert_template_file(
            data={
                "entity": source,
            }
        ) as (actual, _):
            assert contained_by_source.id in actual
