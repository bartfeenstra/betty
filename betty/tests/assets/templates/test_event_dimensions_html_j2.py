from betty.ancestry import Event, Place, PlaceName, Citation, Source, Birth
from betty.asyncio import sync
from betty.locale import Date
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'event-dimensions.html.j2'

    @sync
    async def test_without_meta(self):
        event = Event(Birth())
        expected = ''
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_date(self):
        event = Event(Birth())
        event.date = Date(1970)
        expected = '1970'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_place(self):
        event = Event(Birth())
        event.place = Place('P0', [PlaceName('The Place')])
        expected = 'in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_place_is_place_context(self):
        event = Event(Birth())
        place = Place('P0', [PlaceName('The Place')])
        event.place = place
        expected = ''
        async with self._render(data={
            'event': event,
            'place_context': place,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_date_and_place(self):
        event = Event(Birth())
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        expected = '1970 in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_citation(self):
        event = Event(Birth())
        event.citations.append(Citation(Source('The Source')))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        event = Event(Birth())
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        event.citations.append(Citation(Source('The Source')))
        expected = '1970 in <address><span>The Place</span></address>'
        async with self._render(data={
            'event': event,
            'embedded': True,
        }) as (actual, _):
            self.assertEqual(expected, actual)
