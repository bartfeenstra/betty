from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/reference.html.j2", data={"citations": []}
    ) as rendered:
        assert rendered == ""


async def test_with_citation(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/reference.html.j2", data={"citations": [Citation(source=Source())]}
    ) as rendered:
        assert rendered == ' <sup><a href="#reference-1">[1]</a></sup>'
