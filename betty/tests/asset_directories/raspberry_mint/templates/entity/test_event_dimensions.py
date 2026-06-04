from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.date import Date
from betty.document import Document, EntityContexts
from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entities.source import Source
from betty.event_types.birth import Birth
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    event = Event(event_type=Birth())
    async with assert_template_file(
        data={
            "event": event,
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == "sometime"


async def test_with_date(assert_template_file: AssertTemplateFile) -> None:
    event = Event(
        event_type=Birth(),
        date=Date(1970),
    )
    expected = "1970"
    async with assert_template_file(
        data={
            "event": event,
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place(assert_template_file: AssertTemplateFile) -> None:
    place = Place(
        id="P0",
        names=[PlaceName("The Place")],
    )
    event = Event(event_type=Birth(), place=place)
    expected = f'in <a href="/place/{place.public_id}/index.html"><span lang="und" dir="auto">The Place</span></a>'
    async with assert_template_file(
        data={
            "event": event,
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place_is_place_context(
    assert_template_file: AssertTemplateFile,
) -> None:
    event = Event(event_type=Birth())
    place = Place(
        id="P0",
        names=[PlaceName("The Place")],
    )
    event.place = place
    async with assert_template_file(
        data={
            "event": event,
            "document": Document(entity_contexts=EntityContexts(place)),
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == "sometime"


async def test_with_date_and_place(assert_template_file: AssertTemplateFile) -> None:
    place = Place(
        id="P0",
        names=[PlaceName("The Place")],
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
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citation(assert_template_file: AssertTemplateFile) -> None:
    event = Event(event_type=Birth())
    event.citations.add(Citation(source=Source(name="The Source")))
    expected = 'sometime <sup><a href="#reference-1">[1]</a></sup>'
    async with assert_template_file(
        data={
            "event": event,
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded(assert_template_file: AssertTemplateFile) -> None:
    event = Event(
        event_type=Birth(),
        date=Date(1970),
    )
    event.place = Place(
        id="P0",
        names=[PlaceName("The Place")],
    )
    event.citations.add(Citation(source=Source(name="The Source")))
    expected = '1970 in <span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "event": event,
            "embedded": True,
        },
        assets={raspberry_mint},
        template="entity/event-dimensions.html.j2",
    ) as (actual, _):
        assert actual == expected
