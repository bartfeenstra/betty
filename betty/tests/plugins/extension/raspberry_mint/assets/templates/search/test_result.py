from betty.ancestry.person import Person
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    entity = Person()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="search/result.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
