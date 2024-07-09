from betty.extension.cotton_candy import CottonCandy
from betty.jinja2 import EntityContexts
from betty.locale import Date
from betty.model.ancestry import Event, Place, PlaceName, Citation, Source
from betty.model.event_type import Birth
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = "event-dimensions.html.j2"

    async def test_without_meta(self) -> None:
        event = Event(event_type=Birth)
        expected = ""
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_date(self) -> None:
        event = Event(
            event_type=Birth,
            date=Date(1970),
        )
        expected = "1970"
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_place(self) -> None:
        event = Event(event_type=Birth)
        event.place = Place(
            id="P0",
            names=[PlaceName(name="The Place")],
        )
        expected = (
            'in <span><a href="/place/P0/index.html"><span>The Place</span></a></span>'
        )
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_place_is_place_context(self) -> None:
        event = Event(event_type=Birth)
        place = Place(
            id="P0",
            names=[PlaceName(name="The Place")],
        )
        event.place = place
        expected = ""
        async with self._render(
            data={
                "event": event,
                "entity_contexts": EntityContexts(place),
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_date_and_place(self) -> None:
        event = Event(
            event_type=Birth,
            date=Date(1970),
        )
        event.place = Place(
            id="P0",
            names=[PlaceName(name="The Place")],
        )
        expected = '1970 in <span><a href="/place/P0/index.html"><span>The Place</span></a></span>'
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_citation(self) -> None:
        event = Event(event_type=Birth)
        event.citations.add(Citation(source=Source(name="The Source")))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        async with self._render(
            data={
                "event": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_embedded(self) -> None:
        event = Event(
            event_type=Birth,
            date=Date(1970),
        )
        event.place = Place(
            id="P0",
            names=[PlaceName(name="The Place")],
        )
        event.citations.add(Citation(source=Source(name="The Source")))
        expected = "1970 in <span><span>The Place</span></span>"
        async with self._render(
            data={
                "event": event,
                "embedded": True,
            }
        ) as (actual, _):
            assert expected == actual
