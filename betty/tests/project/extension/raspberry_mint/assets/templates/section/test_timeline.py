from betty.ancestry.event import Event
from betty.date import Date
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "events": [],
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/timeline.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_events() -> None:
    event = Event(id="E0", date=Date(1970, 1, 1))
    async with assert_template_file(
        data={
            "events": [event],
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/timeline.html.j2",
    ) as (actual, _):
        assert event.public_id in actual
