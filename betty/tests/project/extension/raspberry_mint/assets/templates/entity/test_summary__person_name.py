from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/summary--person-name.html.j2"

    async def test_minimal(self) -> None:
        person_name = PersonName(person=Person(), individual="Jane")
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ):
            pass
