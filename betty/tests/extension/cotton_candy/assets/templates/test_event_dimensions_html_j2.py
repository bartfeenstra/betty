from betty.ancestry import Event, Citation, Source
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.date import Date
from betty.extension.cotton_candy import CottonCandy
from betty.jinja2 import EntityContexts
from betty.test_utils.assets.templates import TemplateTestBase


class Test(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "event-dimensions.html.j2"

    async def test_without_meta(self) -> None:
        event = Event(event_type=Birth())
        expected = ""
        async with self._render(
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
        async with self._render(
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
        expected = 'in <span><a href="/place/P0/index.html"><span lang="und">The Place</span></a></span>'
        async with self._render(
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
        async with self._render(
            data={
                "event": event,
                "entity_contexts": EntityContexts(place),
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
        expected = '1970 in <span><a href="/place/P0/index.html"><span lang="und">The Place</span></a></span>'
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_citation(self) -> None:
        event = Event(event_type=Birth())
        event.citations.add(Citation(source=Source(name="The Source")))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        async with self._render(
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
        expected = '1970 in <span><span lang="und">The Place</span></span>'
        async with self._render(
            data={
                "event": event,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected
