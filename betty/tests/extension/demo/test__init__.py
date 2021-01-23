from tempfile import TemporaryDirectory

from betty.app import App
from betty.asyncio import sync
from betty.config import Configuration
from betty.extension.demo import Demo
from betty.load import load
from betty.tests import TestCase


class DemoTest(TestCase):
    @sync
    async def test_load(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.extensions[Demo] = None
            async with App(configuration) as app:
                await load(app)
            self.assertNotEqual(0, len(app.ancestry.people))
            self.assertNotEqual(0, len(app.ancestry.places))
            self.assertNotEqual(0, len(app.ancestry.events))
            self.assertNotEqual(0, len(app.ancestry.sources))
            self.assertNotEqual(0, len(app.ancestry.citations))
