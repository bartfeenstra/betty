from betty.app import App
from betty.generate import generate
from betty.project import ProjectExtensionConfiguration
from betty.tests import patch_cache
from betty.trees import Trees


class TestTrees:
    @patch_cache
    async def test_post_generate_event(self):
        with App() as app:
            app.project.configuration.debug = True
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Trees))
            await generate(app)
        with open(app.project.configuration.www_directory_path / 'trees.js', encoding='utf-8') as f:
            betty_js = f.read()
        assert 'trees.js' in betty_js
        with open(app.project.configuration.www_directory_path / 'trees.css', encoding='utf-8') as f:
            betty_css = f.read()
        assert '.tree' in betty_css
