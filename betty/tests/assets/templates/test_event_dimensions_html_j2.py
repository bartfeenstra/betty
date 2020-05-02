from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Event, Place, LocalizedName, Citation, Source, Birth
from betty.config import Configuration
from betty.functools import sync
from betty.locale import Date
from betty.site import Site


class Test(TestCase):
    async def _render(self, **data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                return await site.jinja2_environment.get_template('event-dimensions.html.j2').render_async(**data)

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
        event.place = Place('P0', [LocalizedName('The Place')])
        expected = 'in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_place_is_place_context(self):
        event = Event(Birth())
        place = Place('P0', [LocalizedName('The Place')])
        event.place = place
        expected = ''
        actual = await self._render(event=event, place_context=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_date_and_place(self):
        event = Event(Birth())
        event.date = Date(1970)
        event.place = Place('P0', [LocalizedName('The Place')])
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
        event.place = Place('P0', [LocalizedName('The Place')])
        event.citations.append(Citation(Source('The Source')))
        expected = '1970 in <address><span>The Place</span></address>'
        actual = await self._render(event=event, embedded=True)
        self.assertEqual(expected, actual)
