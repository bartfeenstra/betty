from betty.ancestry.source import Source
from betty.extension.raspberry_mint import RaspberryMint
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    entity = Source()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="search/result--source.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
