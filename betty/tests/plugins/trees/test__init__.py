from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.plugins.trees import Trees
from betty.render import render
from betty.site import Site


class TreeTest(TestCase):
    def test_post_render_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://ancestry.example.com')
            configuration.mode = 'development'
            configuration.plugins[Trees] = {}
            site = Site(configuration)
            render(site)
            with open(join(configuration.www_directory_path, 'betty.js')) as f:
                betty_js = f.read()
            self.assertIn('trees.js', betty_js)
            self.assertIn('trees.css', betty_js)
            with open(join(configuration.www_directory_path, 'betty.css')) as f:
                betty_css = f.read()
            self.assertIn('.tree', betty_css)
