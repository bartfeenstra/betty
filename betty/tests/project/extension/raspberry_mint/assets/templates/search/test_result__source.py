from betty.ancestry.source import Source
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


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
