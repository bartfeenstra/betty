from betty.ancestry.event import Event
from betty.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    event = Event()
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={RaspberryMint},
        template="entity/summary--event.html.j2",
    ) as (actual, _):
        assert actual
