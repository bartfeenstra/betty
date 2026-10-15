from betty.entities.source import Source
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--source.html.j2", data={"entity": source}
    ) as rendered:
        assert rendered


async def test_with_contained_by(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--source.html.j2", data={"entity": source}
    ) as rendered:
        assert contained_by_source.id in rendered
