from betty.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    url = "https://example.com/per/ma.link"
    async with assert_template_file(
        data={
            "url": url,
        },
        extensions={RaspberryMint},
        template="component/permalink.html.j2",
    ) as (actual, _):
        assert "<a " in actual
        assert url in actual
