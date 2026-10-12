from betty.entities.place import Place
from betty.localizer import default_localizer
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = Place()
    async with assert_raspberry_mint_jinja_file(
        "search/result--place.html.j2", data={"entity": entity}
    ) as rendered:
        assert entity.label.localize(default_localizer) in rendered
        assert entity.id in rendered
