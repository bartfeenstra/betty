from betty.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        extensions={RaspberryMint}, template="entity/private.html.j2"
    ):
        pass
