from betty.ancestry.place import Place
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    place = Place()
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
        template="search/result--place.html.j2",
    ) as (actual, _):
        assert place.label.localize(DEFAULT_LOCALIZER) in actual
        assert place.public_id in actual
