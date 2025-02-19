from betty.ancestry.source import Source
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "search/result--source.html.j2"

    async def test_minimal(self) -> None:
        source = Source()
        async with self.assert_template_file(
            data={
                "entity": source,
            }
        ) as (actual, _):
            assert source.label.localize(DEFAULT_LOCALIZER) in actual
            assert source.id in actual
