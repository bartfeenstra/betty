from os import path
from tempfile import TemporaryDirectory

from betty.config import Configuration
from betty.asyncio import sync
from betty.extension.redoc import ReDoc
from betty.generate import generate
from betty.app import App
from betty.tests import patch_cache, TestCase


class ReDocTest(TestCase):
    @patch_cache
    @sync
    async def test(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            configuration.extensions[ReDoc] = None
            async with App(configuration) as app:
                await generate(app)
            self.assertTrue(path.isfile(path.join(output_directory_path, 'www', 'api', 'index.html')))
            self.assertTrue(path.isfile(path.join(output_directory_path, 'www', 'redoc.js')))
