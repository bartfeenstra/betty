from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert source.id in rendered


async def test_with_private_source(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source(privacy=Privacy.PRIVATE)
    citation = Citation(source=source)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert source.id not in rendered
