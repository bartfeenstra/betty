from betty.ancestry.person import Person
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.test_utils.jinja2 import assert_template_file


async def test() -> None:
    person = Person()
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint.plugin, Trees.plugin},
        template="section/tree.html.j2",
    ) as (actual, _):
        assert actual
