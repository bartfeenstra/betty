from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Place, LocalizedName
from betty.config import Configuration
from betty.functools import sync
from betty.site import Site


class Test(TestCase):
    async def _render(self, **data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                return await site.jinja2_environment.get_template('label/place.html.j2').render_async(**data)

    @sync
    async def test(self):
        place = Place('P0', [LocalizedName('The Place')])
        expected = '<address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        actual = await self._render(place=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_name_with_locale(self):
        place = Place('P0', [LocalizedName('The Place', 'en')])
        expected = '<address><a href="/place/P0/index.html"><span lang="en">The Place</span></a></address>'
        actual = await self._render(place=place)
        self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        place = Place('P0', [LocalizedName('The Place')])
        expected = '<address><span>The Place</span></address>'
        actual = await self._render(place=place, embedded=True)
        self.assertEqual(expected, actual)
