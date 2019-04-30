from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.plugins.maps import Maps
from betty.render import render
from betty.site import Site


class RenderTest(TestCase):
    _outputDirectory = None
    site = None

    @classmethod
    def setUpClass(cls):
        ancestry = Ancestry()
        cls._outputDirectory = TemporaryDirectory()
        configuration = Configuration(
            None, cls._outputDirectory.name, 'https://ancestry.example.com')
        configuration.plugins[Maps] = {}
        cls.site = Site(ancestry, configuration)
        render(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._outputDirectory.cleanup()

    def test_betty_js(self):
        with open(join(self.__class__._outputDirectory.name, 'betty.js')) as f:
            betty_js = f.read()
        self.assertIn('maps.js', betty_js)
        self.assertIn('maps.css', betty_js)

    def test_betty_css(self):
        with open(join(self.__class__._outputDirectory.name, 'betty.css')) as f:
            betty_css = f.read()
        self.assertIn('.map', betty_css)
