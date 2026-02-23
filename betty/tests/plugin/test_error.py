from __future__ import annotations

from betty.plugin.error import PluginNotFound, PluginTypeNotFound
from betty.test_utils.plugin import DummyPluginDefinition


class TestPluginTypeNotFound:
    def test__without_available_plugin_types(self) -> None:
        unknown_plugin_type = "my-first-plugin-type-id"
        sut = PluginTypeNotFound(unknown_plugin_type, [])
        assert unknown_plugin_type in str(sut)

    def test__with_available_plugin_types(self) -> None:
        unknown_plugin_type = "my-first-plugin-type-id"
        available_plugin_type = "my-first-available-plugin-type-id"
        sut = PluginTypeNotFound(unknown_plugin_type, [available_plugin_type])
        assert unknown_plugin_type in str(sut)
        assert available_plugin_type in str(sut)


class TestPluginNotFound:
    def test__without_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        sut = PluginNotFound(DummyPluginDefinition, unknown_plugin, [])
        assert unknown_plugin in str(sut)

    def test__with_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        available_plugin = "my-first-available-plugin-id"
        sut = PluginNotFound(DummyPluginDefinition, unknown_plugin, [available_plugin])
        assert unknown_plugin in str(sut)
        assert available_plugin in str(sut)
