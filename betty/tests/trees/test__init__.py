from betty.asyncio import sync
from betty.generate import generate
from betty.trees import Trees
from betty.app import App, AppExtensionConfiguration
from betty.tests import patch_cache, TestCase


class TreesTest(TestCase):
    @patch_cache
    @sync
    async def test_post_generate_event(self):
        async with App() as app:
            app.configuration.debug = True
            app.configuration.extensions.add(AppExtensionConfiguration(Trees))
            await generate(app)
        with open(app.configuration.www_directory_path / 'trees.js', encoding='utf-8') as f:
            betty_js = f.read()
        self.assertIn('trees.js', betty_js)
        with open(app.configuration.www_directory_path / 'trees.css', encoding='utf-8') as f:
            betty_css = f.read()
        self.assertIn('.tree', betty_css)
