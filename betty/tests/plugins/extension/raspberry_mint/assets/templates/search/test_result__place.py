from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.place import Place
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    entity = Place()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="search/result--place.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
