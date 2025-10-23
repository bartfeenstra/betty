from betty.ancestry.person import Person
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    person = Person()
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="search/result--person.html.j2",
    ) as (actual, _):
        assert person.label.localize(DEFAULT_LOCALIZER) in actual
        assert person.public_id in actual
