from unittest.mock import Mock

from betty.extension import Extension
from betty.app import App
from betty.tests import TestCase


class ExtensionTest(TestCase):
    def test_new_for_app(self):
        app = Mock(App)
        extension = Extension.new_for_app(app)
        self.assertIsInstance(extension, Extension)

    def test_depends_on(self):
        self.assertEquals(set(), Extension.depends_on())
