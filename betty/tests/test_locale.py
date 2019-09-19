from typing import Optional
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import PlaceName, Place
from betty.locale import _score, Locale, sort


class ScoreTest(TestCase):
    @parameterized.expand([
        (0, None, None),
        (0, Locale('nl'), Locale('en')),
        (1, Locale('nl'), Locale('nl')),
        (1, Locale('nl', 'NL'), Locale('nl', 'BE')),
        (2, Locale('nl', 'NL'), Locale('nl', 'NL')),
        (2, Locale('nl', 'NL', 'Latn'), Locale('nl', 'NL', 'Brai')),
        (3, Locale('nl', 'NL', 'Latn'), Locale('nl', 'NL', 'Latn')),
        (3, Locale('nl', 'NL', 'Latn', 'twd'), Locale('nl', 'NL', 'Latn', 'dru')),
        (4, Locale('nl', 'NL', 'Latn', 'twd'), Locale('nl', 'NL', 'Latn', 'twd')),
    ])
    def test(self, expected: int, locale_1: Optional[Locale], locale_2: Optional[Locale]):
        self.assertEquals(expected, _score(locale_1, locale_2))


class SortTest(TestCase):
    @parameterized.expand([
        ([PlaceName('Nederland', Locale('nl')), PlaceName('The Netherlands', Locale('en'))], [
         PlaceName('The Netherlands', Locale('en')), PlaceName('Nederland', Locale('nl'))], Locale('nl')),
    ])
    def test(self, expected, names, locale: Locale):
        place = Place('The Place', names)
        self.assertEquals(expected, sort(place.names, locale))
