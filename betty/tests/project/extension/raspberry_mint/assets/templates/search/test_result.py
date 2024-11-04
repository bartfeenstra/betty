from betty.ancestry.person import Person
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "search/result.html.j2"

    async def test_minimal(self) -> None:
        entity = Person()
        async with self.assert_template_file(
            data={
                "entity": entity,
            }
        ) as (actual, _):
            assert entity.label.localize(DEFAULT_LOCALIZER) in actual
            assert entity.id in actual
