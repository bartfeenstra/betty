from betty.ancestry.source import Source
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    source = Source()
    async with assert_template_file(
        data={
            "entity": source,
        },
        extensions={RaspberryMint},
        template="search/result--source.html.j2",
    ) as (actual, _):
        assert source.label.localize(DEFAULT_LOCALIZER) in actual
        assert source.public_id in actual
