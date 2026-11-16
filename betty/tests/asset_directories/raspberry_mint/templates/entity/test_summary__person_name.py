from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person_name = PersonName(person=Person(), individual="Jane")
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered
