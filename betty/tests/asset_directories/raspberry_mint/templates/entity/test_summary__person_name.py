from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    person_name = PersonName(person=Person(), individual="Jane")
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        assets={RASPBERRY_MINT},
        template="entity/summary--person-name.html.j2",
    ):
        pass
