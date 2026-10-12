from betty.entities.person import Person
from betty.localizer import default_localizer
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = Person()
    async with assert_raspberry_mint_jinja_file(
        "search/result.html.j2", data={"entity": entity}
    ) as rendered:
        assert entity.label.localize(default_localizer) in rendered
        assert entity.id in rendered
