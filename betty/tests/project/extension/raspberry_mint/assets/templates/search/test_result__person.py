from betty.ancestry.person import Person
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "search/result--person.html.j2"

    async def test_minimal(self) -> None:
        person = Person()
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert person.label.localize(DEFAULT_LOCALIZER) in actual
            assert person.id in actual
