from unittest import TestCase

from betty.plugin import Plugin, name, from_configuration_list, CyclicDependencyError, PluginNotFoundError


class FruitPlugin(Plugin):
    pass


class RoundFruitPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [FruitPlugin]


class ApplePlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [RoundFruitPlugin]


class BentFruitPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [FruitPlugin]


class BananaPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [BentFruitPlugin]


class KiwiPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [MangoPlugin]


class MangoPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return [KiwiPlugin]


class TestFromConfigurationList(TestCase):
    def test_without_plugins(self):
        self.assertEquals([], from_configuration_list([]))

    def test_with_one_plugin(self):
        actual = from_configuration_list({
            name(FruitPlugin): {},
        })
        self.assertEquals(1, len(actual))
        self.assertIsInstance(actual[0], FruitPlugin)

    def test_with_multiple_plugins_with_duplicate_dependencies(self):
        actual = from_configuration_list({
            name(ApplePlugin): {},
            name(BananaPlugin): {},
        })
        self.assertEquals(3, len(actual))
        # @todo THis fails, because the original configuration comes from dictionaries, WHICH ARE NOT ORDERED IN JSON OR OLDER PYTHON VERSIONS.....
        self.assertIsInstance(actual[0], FruitPlugin)
        self.assertIsInstance(actual[1], ApplePlugin)
        self.assertIsInstance(actual[2], BananaPlugin)

    def test_with_multiple_plugins_with_cyclic_dependencies(self):
        with self.assertRaises(CyclicDependencyError):
            from_configuration_list({
                name(KiwiPlugin): {},
                name(MangoPlugin): {},
            })

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
