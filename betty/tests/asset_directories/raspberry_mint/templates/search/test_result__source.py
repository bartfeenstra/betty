from betty.entities.source import Source
from betty.localizer import default_localizer
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = Source()
    async with assert_raspberry_mint_jinja_file(
        "search/result--source.html.j2", data={"entity": entity}
    ) as rendered:
        assert entity.label.localize(default_localizer) in rendered
        assert entity.id in rendered
