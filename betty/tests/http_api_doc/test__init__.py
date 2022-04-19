from betty.asyncio import sync
from betty.http_api_doc import HttpApiDoc
from betty.generate import generate
from betty.app import App
from betty.project import ProjectExtensionConfiguration
from betty.tests import patch_cache, TestCase


class HttpApiDocTest(TestCase):
    @patch_cache
    @sync
    async def test(self):
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(HttpApiDoc))
            await generate(app)
            self.assertTrue((app.project.configuration.www_directory_path / 'api' / 'index.html').is_file())
            self.assertTrue((app.project.configuration.www_directory_path / 'http-api-doc.js').is_file())
