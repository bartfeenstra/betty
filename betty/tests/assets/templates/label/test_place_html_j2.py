from parameterized import parameterized

from betty.ancestry import Place, PlaceName
from betty.functools import sync
from betty.locale import DateRange, Date
from betty.tests.assets.templates import TemplateTestCase


class Test(TemplateTestCase):
    template = 'label/place.html.j2'

    @parameterized.expand([
        ('<address><a href="/place/P0/index.html"><span>The Place</span></a></address>',
         {
             'place': Place('P0', [PlaceName('The Place')]),
         }),
        ('<address><a href="/place/P0/index.html"><span lang="en">The Place</span></a></address>',
         {
             'place': Place('P0', [PlaceName('The Place', 'en')]),
         }),
        ('<address><a href="/place/P0/index.html"><span lang="nl">De Plaats</span></a></address>',
         {
             'place': Place('P0', [PlaceName('The Place', 'en'), PlaceName('De Plaats', 'nl')]),
             'locale': 'nl',
         }),
        ('<address><span>The Place</span></address>',
         {
             'place': Place('P0', [PlaceName('The Place')]),
             'embedded': True,
         }),
        ('<address><a href="/place/P0/index.html"><span lang="nl">De Nieuwe Plaats</span></a></address>',
         {
             'place': Place('P0', [PlaceName('The Old Place', 'en', date=DateRange(None, Date(1969, 12, 31))),
                                   PlaceName('De Nieuwe Plaats', 'nl', date=DateRange(Date(1970, 1, 1)))]),
             'locale': 'nl',
             'date_context': Date(1970, 1, 1),
         })
    ])
    @sync
    async def test(self, expected, data):
        actual = await self._render(**data)
        self.assertEqual(expected, actual)
