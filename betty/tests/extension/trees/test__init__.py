from tempfile import TemporaryDirectory

from betty.config import Configuration, ExtensionConfiguration
from betty.asyncio import sync
from betty.generate import generate
from betty.extension.trees import Trees
from betty.app import App
from betty.tests import patch_cache, TestCase


class TreesTest(TestCase):
    @patch_cache
    @sync
    async def test_post_render_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            configuration.mode = 'development'
            configuration.extensions.add(ExtensionConfiguration(Trees))
            async with App(configuration) as app:
                await generate(app)
            with open(configuration.www_directory_path / 'trees.js', encoding='utf-8') as f:
                betty_js = f.read()
            self.assertIn('trees.js', betty_js)
            self.assertIn('trees.css', betty_js)
            with open(configuration.www_directory_path / 'trees.css', encoding='utf-8') as f:
                betty_css = f.read()
            self.assertIn('.tree', betty_css)
