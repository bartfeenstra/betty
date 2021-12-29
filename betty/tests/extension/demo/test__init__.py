from tempfile import TemporaryDirectory

from betty.app import App
from betty.asyncio import sync
from betty.config import Configuration, ExtensionConfiguration
from betty.extension.demo import Demo
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.tests import TestCase


class DemoTest(TestCase):
    @sync
    async def test_load(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.extensions.add(ExtensionConfiguration(Demo))
            async with App(configuration) as app:
                await load(app)
            self.assertNotEqual(0, len(app.ancestry.entities[Person]))
            self.assertNotEqual(0, len(app.ancestry.entities[Place]))
            self.assertNotEqual(0, len(app.ancestry.entities[Event]))
            self.assertNotEqual(0, len(app.ancestry.entities[Source]))
            self.assertNotEqual(0, len(app.ancestry.entities[Citation]))
