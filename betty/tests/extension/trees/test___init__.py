from betty.app import App
from betty.asyncio import sync
from betty.extension import Trees
from betty.generate import generate
from betty.project import ExtensionConfiguration
from betty.tests import patch_cache


class TestTrees:
    @patch_cache
    @sync
    async def test_generate(self) -> None:
        with App() as app:
            app.project.configuration.debug = True
            app.project.configuration.extensions.append(ExtensionConfiguration(Trees))
            await generate(app)
        with open(app.project.configuration.www_directory_path / 'trees.js', encoding='utf-8') as f:
            betty_js = f.read()
        assert 'trees.js' in betty_js
        with open(app.project.configuration.www_directory_path / 'trees.css', encoding='utf-8') as f:
            betty_css = f.read()
        assert '.tree' in betty_css
