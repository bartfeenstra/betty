from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.functools import sync
from betty.generate import generate
from betty.plugin.maps import Maps
from betty.site import Site
from betty.tests import patch_cache


class MapsTest(TestCase):
    @patch_cache
    @sync
    async def test_post_render_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://ancestry.example.com')
            configuration.mode = 'development'
            configuration.plugins[Maps] = None
            async with Site(configuration) as site:
                await generate(site)
            with open(join(configuration.www_directory_path, 'js', 'maps.js')) as f:
                maps_js = f.read()
            self.assertIn('maps.js', maps_js)
            self.assertIn('maps.css', maps_js)
            with open(join(configuration.www_directory_path, 'css', 'maps.css')) as f:
                maps_css = f.read()
            self.assertIn('.map', maps_css)
