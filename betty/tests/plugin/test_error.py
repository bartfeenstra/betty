from __future__ import annotations

from betty.plugin.error import PluginNotFound
from betty.test_utils.plugin import DummyPluginDefinition


class TestPluginNotFound:
    async def test_new__without_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        sut = PluginNotFound(DummyPluginDefinition.type, unknown_plugin, [])
        assert unknown_plugin in str(sut)

    async def test_new__with_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        available_plugin = "my-first-available-plugin-id"
        sut = PluginNotFound(
            DummyPluginDefinition.type, unknown_plugin, [available_plugin]
        )
        assert unknown_plugin in str(sut)
        assert available_plugin in str(sut)
