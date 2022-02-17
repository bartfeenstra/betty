from pathlib import Path
from tempfile import TemporaryDirectory

from betty.config import Configuration, ExtensionConfiguration
from betty.asyncio import sync
from betty.extension.http_api_doc import HttpApiDoc
from betty.generate import generate
from betty.app import App
from betty.tests import patch_cache, TestCase


class HttpApiDocTest(TestCase):
    @patch_cache
    @sync
    async def test(self):
        with TemporaryDirectory() as output_directory_path_str:
            output_directory_path = Path(output_directory_path_str)
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            configuration.extensions.add(ExtensionConfiguration(HttpApiDoc))
            async with App(configuration) as app:
                await generate(app)
            self.assertTrue((output_directory_path / 'www' / 'api' / 'index.html').is_file())
            self.assertTrue((output_directory_path / 'www' / 'http-api-doc.js').is_file())
