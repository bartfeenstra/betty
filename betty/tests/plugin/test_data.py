import pytest

from betty.machine_name import InvalidMachineName
from betty.plugin.data import PluginIdDefinition
from betty.plugin.error import PluginNotFound
from betty.service.level.universal import universe
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestPluginIdDefinition:
    def test_load__without_valid_machine_name(self) -> None:
        sut = PluginIdDefinition(DummyPluginDefinition)
        with pytest.raises(InvalidMachineName):
            sut.porter.load("invalid_machine_name")

    def test_load__with_valid_machine_name(self) -> None:
        plugin_id = DummyPluginOne.plugin().id
        sut = PluginIdDefinition(DummyPluginDefinition)
        assert sut.porter.load(plugin_id) == plugin_id

    def test_dump(self) -> None:
        plugin_id = DummyPluginOne.plugin().id
        sut = PluginIdDefinition(DummyPluginDefinition)
        assert sut.porter.dump(plugin_id) == plugin_id

    async def test_hydrate(self) -> None:
        sut = PluginIdDefinition(DummyPluginDefinition)
        await sut.hydrate(universe, DummyPluginOne.plugin().id)

    async def test_hydrate__plugin_not_found(self) -> None:
        sut = PluginIdDefinition(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            await sut.hydrate(universe, "non-existent-plugin-id")


class TestPluginConfigurationDefinition:
    pass
