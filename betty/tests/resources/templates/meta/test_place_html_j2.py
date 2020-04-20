from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import LocalizedName, Place
from betty.config import Configuration
from betty.functools import sync
from betty.site import Site


class Test(TestCase):
    maxDiff = None

    async def _render(self, **data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                return await site.jinja2_environment.get_template('meta/place.html.j2').render_async(**data)

    @sync
    async def test_without_enclosing_places(self):
        place = Place('P0', [LocalizedName('The Place')])
        expected = ''
        actual = await self._render(place=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_without_place_context(self):
        place = Place('P0', [LocalizedName('The Place')])
        enclosing_place = Place('P1', [LocalizedName('The Enclosing Place')])
        place.enclosed_by = enclosing_place
        all_enclosing_place = Place('P2', [LocalizedName('The All-enclosing Place')])
        enclosing_place.enclosed_by = all_enclosing_place
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address>, <address><a href="/place/P2/index.html"><span>The All-enclosing Place</span></a></address></div>'
        actual = await self._render(place=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_with_matching_place_context(self):
        place = Place('P0', [LocalizedName('The Place')])
        enclosing_place = Place('P1', [LocalizedName('The Enclosing Place')])
        place.enclosed_by = enclosing_place
        all_enclosing_place = Place('P2', [LocalizedName('The All-enclosing Place')])
        enclosing_place.enclosed_by = all_enclosing_place
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address></div>'
        actual = await self._render(place=place, place_context=all_enclosing_place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_with_non_matching_place_context(self):
        place = Place('P0', [LocalizedName('The Place')])
        enclosing_place = Place('P1', [LocalizedName('The Enclosing Place')])
        place.enclosed_by = enclosing_place
        all_enclosing_place = Place('P2', [LocalizedName('The All-enclosing Place')])
        enclosing_place.enclosed_by = all_enclosing_place
        unrelated_place = Place('P999', [LocalizedName('Far Far Away')])
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address>, <address><a href="/place/P2/index.html"><span>The All-enclosing Place</span></a></address></div>'
        actual = await self._render(place=place, place_context=unrelated_place)
        self.assertEqual(expected, actual)
