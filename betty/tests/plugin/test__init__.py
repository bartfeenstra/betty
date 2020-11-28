from unittest.mock import Mock

from betty.plugin import Plugin
from betty.site import Site
from betty.tests import TestCase


class PluginTest(TestCase):
    def test_for_site(self):
        site = Mock(Site)
        plugin = Plugin.for_site(site)
        self.assertIsInstance(plugin, Plugin)

    def test_depends_on(self):
        self.assertEquals(set(), Plugin.depends_on())
