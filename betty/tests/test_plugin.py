from typing import Dict
from unittest import TestCase

from betty.graph import CyclicGraphError
from betty.plugin import Plugin, name, from_configuration_list, PluginNotFoundError


class PluginTest(TestCase):
    def test_from_configuration_dict(self):
        plugin = Plugin.from_configuration_dict({})
        self.assertIsInstance(plugin, Plugin)

    def test_depends_on(self):
        self.assertEquals(set(), Plugin.depends_on())

    def test_subscribes_to(self):
        plugin = Plugin.from_configuration_dict({})
        self.assertEquals(set(), plugin.subscribes_to())


class NonConfigurablePlugin(Plugin):
    pass


class ConfigurablePlugin(Plugin):
    def __init__(self, check):
        self.check = check

    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls(configuration['check'])


class DependsOnNonConfigurablePluginPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {NonConfigurablePlugin}


class AlsoDependsOnNonConfigurablePluginPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {NonConfigurablePlugin}


class DependsOnNonConfigurablePluginPluginPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {DependsOnNonConfigurablePluginPlugin}


class CyclicDependencyOnePlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {CyclicDependencyTwoPlugin}


class CyclicDependencyTwoPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {CyclicDependencyOnePlugin}


class FromConfigurationListTest(TestCase):
    def test_without_plugins(self):
        self.assertEquals([], from_configuration_list([]))

    def test_with_one_plugin(self):
        actual = from_configuration_list([
            name(NonConfigurablePlugin),
        ])
        self.assertEquals(1, len(actual))
        self.assertIsInstance(actual[0], NonConfigurablePlugin)

    def test_with_one_plugin_without_configuration(self):
        actual = from_configuration_list([
            {
                'type': name(NonConfigurablePlugin),
            },
        ])
        self.assertEquals(1, len(actual))
        self.assertIsInstance(actual[0], NonConfigurablePlugin)

    def test_with_one_plugin_with_unneeded_configuration(self):
        actual = from_configuration_list([
            {
                'type': name(NonConfigurablePlugin),
                'configuration': {},
            },
        ])
        self.assertEquals(1, len(actual))
        self.assertIsInstance(actual[0], NonConfigurablePlugin)

    def test_with_one_plugin_with_configuration(self):
        check = 1337
        actual = from_configuration_list([
            {
                'type': name(ConfigurablePlugin),
                'configuration': {
                    'check': check,
                },
            },
        ])
        self.assertEquals(1, len(actual))
        self.assertIsInstance(actual[0], ConfigurablePlugin)
        self.assertEquals(actual[0].check, check)

    def test_with_one_plugin_with_single_chained_dependency(self):
        actual = from_configuration_list([
            name(DependsOnNonConfigurablePluginPluginPlugin),
        ])
        self.assertEquals(3, len(actual))
        self.assertIsInstance(actual[0], DependsOnNonConfigurablePluginPluginPlugin)
        self.assertIsInstance(actual[1], DependsOnNonConfigurablePluginPlugin)
        self.assertIsInstance(actual[2], NonConfigurablePlugin)

    def test_with_multiple_plugins_with_duplicate_dependencies(self):
        actual = from_configuration_list([
            name(DependsOnNonConfigurablePluginPlugin),
            name(AlsoDependsOnNonConfigurablePluginPlugin),
        ])
        self.assertEquals(3, len(actual))
        self.assertIn(DependsOnNonConfigurablePluginPlugin, [type(plugin) for plugin in actual])
        self.assertIn(AlsoDependsOnNonConfigurablePluginPlugin, [type(plugin) for plugin in actual])
        self.assertIsInstance(actual[2], NonConfigurablePlugin)

    def test_with_multiple_plugins_with_cyclic_dependencies(self):
        with self.assertRaises(CyclicGraphError):
            from_configuration_list([
                name(CyclicDependencyOnePlugin),
            ])

    def test_with_multiple_plugins_with_unknown_plugin_type_module(self):
        with self.assertRaises(PluginNotFoundError):
            from_configuration_list({
                'foo.bar.Baz': {},
            })

    def test_with_multiple_plugins_with_unknown_plugin_type_class(self):
        with self.assertRaises(PluginNotFoundError):
            from_configuration_list({
                '%s.Foo' % self.__module__: {},
            })
