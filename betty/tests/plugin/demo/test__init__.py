from tempfile import TemporaryDirectory

from betty.site import Site
from betty.asyncio import sync
from betty.config import Configuration
from betty.plugin.demo import Demo
from betty.parse import parse
from betty.tests import TestCase


class DemoTest(TestCase):
    @sync
    async def test_load(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.plugins[Demo] = None
            async with Site(configuration) as site:
                await parse(site)
            self.assertNotEqual(0, len(site.ancestry.people))
            self.assertNotEqual(0, len(site.ancestry.places))
            self.assertNotEqual(0, len(site.ancestry.events))
            self.assertNotEqual(0, len(site.ancestry.sources))
            self.assertNotEqual(0, len(site.ancestry.citations))
