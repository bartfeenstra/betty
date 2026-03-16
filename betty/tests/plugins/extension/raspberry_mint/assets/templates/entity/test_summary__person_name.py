from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    person_name = PersonName(person=Person(), individual="Jane")
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/summary--person-name.html.j2",
    ):
        pass
