from unittest import TestCase

from betty.ancestry import Link
from betty.plugins.wikipedia import _retrieve_one


class WikipediaTest(TestCase):
    def test_retrieve_one(self):
        link = Link('https://en.wikipedia.org/wiki/Amsterdam')
        _retrieve_one(link)
