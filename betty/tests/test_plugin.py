from unittest import TestCase
from unittest.mock import Mock

from betty.plugin import Plugin
from betty.site import Site


class PluginTest(TestCase):
    def test_from_configuration_dict(self):
        site = Mock(Site)
        plugin = Plugin.from_configuration_dict(site, {})
        self.assertIsInstance(plugin, Plugin)

    def test_depends_on(self):
        self.assertEquals(set(), Plugin.depends_on())

    def test_subscribes_to(self):
        site = Mock(Site)
        plugin = Plugin.from_configuration_dict(site, {})
        self.assertEquals(set(), plugin.subscribes_to())
