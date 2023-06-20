from betty.app import App
from betty.asyncio import sync
from betty.generate import generate
from betty.extension import HttpApiDoc
from betty.project import ExtensionConfiguration
from betty.tests import patch_cache


class TestHttpApiDoc:
    @patch_cache
    @sync
    async def test_generate(self) -> None:
        with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(HttpApiDoc))
            await generate(app)
            assert (app.project.configuration.www_directory_path / 'api' / 'index.html').is_file()
            assert (app.project.configuration.www_directory_path / 'http-api-doc.js').is_file()
