from __future__ import annotations

from betty.locale.localizable import Plain
from betty.plugin.error import PluginNotFound, UnmetRequirement
from betty.requirement import StaticRequirement
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.plugin.classed import ClassedDummyPluginOne


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


class TestUnmetRequirement:
    async def test_new(self) -> None:
        requirement_summary = "My First Requirement"
        sut = UnmetRequirement(
            ClassedDummyPluginOne, StaticRequirement(Plain(requirement_summary))
        )
        actual = str(sut)
        assert ClassedDummyPluginOne.plugin.id in actual
        assert requirement_summary in actual
