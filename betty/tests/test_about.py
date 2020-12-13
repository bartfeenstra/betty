from betty import about
from betty.tests import TestCase


class VersionTest(TestCase):
    def test(self):
        self.assertIsInstance(about.version(), str)
