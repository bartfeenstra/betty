from betty.ancestry import Event, Place, PlaceName, Citation, Source, Birth
from betty.functools import sync
from betty.locale import Date
from betty.tests.assets.templates import TemplateTestCase


class Test(TemplateTestCase):
    template = 'event-dimensions.html.j2'

    @sync
    async def test_without_meta(self):
        event = Event(Birth())
        expected = ''
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_date(self):
        event = Event(Birth())
        event.date = Date(1970)
        expected = '1970'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_place(self):
        event = Event(Birth())
        event.place = Place('P0', [PlaceName('The Place')])
        expected = 'in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_place_is_place_context(self):
        event = Event(Birth())
        place = Place('P0', [PlaceName('The Place')])
        event.place = place
        expected = ''
        actual = await self._render(event=event, place_context=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_date_and_place(self):
        event = Event(Birth())
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        expected = '1970 in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_citation(self):
        event = Event(Birth())
        event.citations.append(Citation(Source('The Source')))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        event = Event(Birth())
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        event.citations.append(Citation(Source('The Source')))
        expected = '1970 in <address><span>The Place</span></address>'
        actual = await self._render(event=event, embedded=True)
        self.assertEqual(expected, actual)
