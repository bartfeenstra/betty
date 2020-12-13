from unittest.mock import Mock

from betty.extension import Extension
from betty.site import Site
from betty.tests import TestCase


class ExtensionTest(TestCase):
    def test_for_site(self):
        site = Mock(Site)
        extension = Extension.for_site(site)
        self.assertIsInstance(extension, Extension)

    def test_depends_on(self):
        self.assertEquals(set(), Extension.depends_on())
