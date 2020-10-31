from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.functools import sync
from betty.generate import generate
from betty.plugin.trees import Trees
from betty.site import Site
from betty.tests import patch_cache


class TreesTest(TestCase):
    @patch_cache
    @sync
    async def test_post_render_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://ancestry.example.com')
            configuration.mode = 'development'
            configuration.plugins[Trees] = None
            async with Site(configuration) as site:
                await generate(site)
            with open(join(configuration.www_directory_path, 'js', 'trees.js')) as f:
                trees_js = f.read()
            self.assertIn('trees.js', trees_js)
            self.assertIn('trees.css', trees_js)
            with open(join(configuration.www_directory_path, 'css', 'trees.css')) as f:
                trees_css = f.read()
            self.assertIn('.tree', trees_css)
