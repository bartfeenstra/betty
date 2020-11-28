from betty.ancestry import PlaceName, Place, Enclosure
from betty.asyncio import sync
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'meta/place.html.j2'

    @sync
    async def test_without_enclosing_places(self):
        place = Place('P0', [PlaceName('The Place')])
        expected = '<div class="meta"></div>'
        async with self._render(data={
            'place': place,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_without_place_context(self):
        place = Place('P0', [PlaceName('The Place')])
        enclosing_place = Place('P1', [PlaceName('The Enclosing Place')])
        Enclosure(place, enclosing_place)
        all_enclosing_place = Place('P2', [PlaceName('The All-enclosing Place')])
        Enclosure(enclosing_place, all_enclosing_place)
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address>, <address><a href="/place/P2/index.html"><span>The All-enclosing Place</span></a></address></div>'
        async with self._render(data={
            'place': place,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_with_matching_place_context(self):
        place = Place('P0', [PlaceName('The Place')])
        enclosing_place = Place('P1', [PlaceName('The Enclosing Place')])
        Enclosure(place, enclosing_place)
        all_enclosing_place = Place('P2', [PlaceName('The All-enclosing Place')])
        Enclosure(enclosing_place, all_enclosing_place)
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address></div>'
        async with self._render(data={
            'place': place,
            'place_context': all_enclosing_place,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_enclosing_place_with_non_matching_place_context(self):
        place = Place('P0', [PlaceName('The Place')])
        enclosing_place = Place('P1', [PlaceName('The Enclosing Place')])
        Enclosure(place, enclosing_place)
        all_enclosing_place = Place('P2', [PlaceName('The All-enclosing Place')])
        Enclosure(enclosing_place, all_enclosing_place)
        unrelated_place = Place('P999', [PlaceName('Far Far Away')])
        expected = '<div class="meta">in <address><a href="/place/P1/index.html"><span>The Enclosing Place</span></a></address>, <address><a href="/place/P2/index.html"><span>The All-enclosing Place</span></a></address></div>'
        async with self._render(data={
            'place': place,
            'place_context': unrelated_place,
        }) as (actual, _):
            self.assertEqual(expected, actual)
