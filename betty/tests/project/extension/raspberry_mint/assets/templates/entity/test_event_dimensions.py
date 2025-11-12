from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.date import Date
from betty.locale.localizable import Plain
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.resource import EntityContexts, new_context
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    event = Event(event_type=Birth())
    async with assert_template_file(
        data={
            "event": event,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == "sometime"


async def test_with_date() -> None:
    event = Event(
        event_type=Birth(),
        date=Date(1970),
    )
    expected = "1970"
    async with assert_template_file(
        data={
            "event": event,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place() -> None:
    place = Place(
        id="P0",
        names=[Name(Plain("The Place"))],
    )
    event = Event(event_type=Birth(), place=place)
    expected = f'in <a href="/place/{place.public_id}/index.html"><span lang="und" dir="auto">The Place</span></a>'
    async with assert_template_file(
        data={
            "event": event,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place_is_place_context() -> None:
    event = Event(event_type=Birth())
    place = Place(
        id="P0",
        names=[Name(Plain("The Place"))],
    )
    event.place = place
    async with assert_template_file(
        data={
            "event": event,
            "resource": new_context(entity_contexts=EntityContexts(place)),
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == "sometime"


async def test_with_date_and_place() -> None:
    place = Place(
        id="P0",
        names=[Name(Plain("The Place"))],
    )
    event = Event(
        event_type=Birth(),
        date=Date(1970),
        place=place,
    )
    expected = f'1970 in <a href="/place/{place.public_id}/index.html"><span lang="und" dir="auto">The Place</span></a>'
    async with assert_template_file(
        data={
            "event": event,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citation() -> None:
    event = Event(event_type=Birth())
    event.citations.add(Citation(source=Source(name=Plain("The Source"))))
    expected = 'sometime <sup><a href="#reference-1">[1]</a></sup>'
    async with assert_template_file(
        data={
            "event": event,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    event = Event(
        event_type=Birth(),
        date=Date(1970),
    )
    event.place = Place(
        id="P0",
        names=[Name(Plain("The Place"))],
    )
    event.citations.add(Citation(source=Source(name=Plain("The Source"))))
    expected = '1970 in <span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "event": event,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected
