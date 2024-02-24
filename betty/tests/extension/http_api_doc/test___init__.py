from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.extension import HttpApiDoc
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestHttpApiDoc:
    async def test_generate(self, binary_file_cache: BinaryFileCache) -> None:
        async with App(binary_file_cache=binary_file_cache) as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(HttpApiDoc))
            await generate(app)
            assert (app.project.configuration.www_directory_path / 'api' / 'index.html').is_file()
            assert (app.project.configuration.www_directory_path / 'http-api-doc.js').is_file()
