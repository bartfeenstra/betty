from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.plugins.js import Js
from betty.render import render
from betty.site import Site


class JsTest(TestCase):
    def test_post_render_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://ancestry.example.com')
            configuration.mode = 'development'
            configuration.plugins[Js] = {}
            site = Site(configuration)
            render(site)
            with open(join(configuration.www_directory_path, 'betty.js')) as f:
                betty_js = f.read()
            self.assertIn('betty.css', betty_js)
            with open(join(configuration.www_directory_path, 'betty.css')) as f:
                betty_css = f.read()
            self.assertGreater(len(betty_css), 0)
