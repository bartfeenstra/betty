from betty.app import App
from betty.generate import generate
from betty.http_api_doc import HttpApiDoc
from betty.project import ExtensionConfiguration
from betty.tests import patch_cache


class TestHttpApiDoc:
    @patch_cache
    async def test(self):
        with App() as app:
            app.project.configuration.extensions.add(ExtensionConfiguration(HttpApiDoc))
            await generate(app)
            assert (app.project.configuration.www_directory_path / 'api' / 'index.html').is_file()
            assert (app.project.configuration.www_directory_path / 'http-api-doc.js').is_file()
