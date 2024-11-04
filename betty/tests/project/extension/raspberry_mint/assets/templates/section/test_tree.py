from betty.ancestry.person import Person
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint, Trees}
    template = "section/tree.html.j2"

    async def test(self) -> None:
        person = Person()
        async with self.assert_template_file(
            data={
                "person": person,
            }
        ) as (actual, _):
            assert actual
