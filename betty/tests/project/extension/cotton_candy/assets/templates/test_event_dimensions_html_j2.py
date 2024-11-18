from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.date import Date
from betty.jinja2 import EntityContexts
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "event-dimensions.html.j2"

    async def test_without_meta(self) -> None:
        event = Event(event_type=Birth())
        expected = ""
        async with self.assert_template_file(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_date(self) -> None:
        event = Event(
            event_type=Birth(),
            date=Date(1970),
        )
        expected = "1970"
        async with self.assert_template_file(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_place(self) -> None:
        event = Event(event_type=Birth())
        event.place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        expected = 'in <span><a href="/place/P0/index.html"><span lang="und" dir="auto">The Place</span></a></span>'
        async with self.assert_template_file(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_place_is_place_context(self) -> None:
        event = Event(event_type=Birth())
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        event.place = place
        expected = ""
        async with self.assert_template_file(
            data={
                "event": event,
                "entity_contexts": await EntityContexts.new(place),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_date_and_place(self) -> None:
        event = Event(
            event_type=Birth(),
            date=Date(1970),
        )
        event.place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        expected = '1970 in <span><a href="/place/P0/index.html"><span lang="und" dir="auto">The Place</span></a></span>'
        async with self.assert_template_file(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_citation(self) -> None:
        event = Event(event_type=Birth())
        event.citations.add(Citation(source=Source(name="The Source")))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        async with self.assert_template_file(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        event = Event(
            event_type=Birth(),
            date=Date(1970),
        )
        event.place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        event.citations.add(Citation(source=Source(name="The Source")))
        expected = '1970 in <span><span lang="und" dir="auto">The Place</span></span>'
        async with self.assert_template_file(
            data={
                "event": event,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected
