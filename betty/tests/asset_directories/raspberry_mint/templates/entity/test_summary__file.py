from betty.entities.file import File
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    file = File(__file__)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--file.html.j2", data={"entity": file}
    ) as rendered:
        assert rendered
