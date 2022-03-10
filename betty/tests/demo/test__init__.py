from betty.app import App
from betty.asyncio import sync
from betty.demo import Demo
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.project import ProjectExtensionConfiguration
from betty.tests import TestCase


class DemoTest(TestCase):
    @sync
    async def test_load(self):
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Demo))
            await load(app)
        self.assertNotEqual(0, len(app.project.ancestry.entities[Person]))
        self.assertNotEqual(0, len(app.project.ancestry.entities[Place]))
        self.assertNotEqual(0, len(app.project.ancestry.entities[Event]))
        self.assertNotEqual(0, len(app.project.ancestry.entities[Source]))
        self.assertNotEqual(0, len(app.project.ancestry.entities[Citation]))
