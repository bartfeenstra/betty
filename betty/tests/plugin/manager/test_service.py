from pytest_mock import MockerFixture

from betty.plugin import PluginTypeRepository
from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.level import UNIVERSE
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestServiceLevelPluginManager:
    def test_types(self) -> None:
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert len(list(sut.types))

    async def test_plugins__with_plugin_type(self) -> None:
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert await sut.plugins(DummyPluginDefinition) is await sut.plugins(
            DummyPluginDefinition
        )
        assert DummyPluginOne.plugin() in await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_plugin_type_id(self, mocker: MockerFixture) -> None:
        plugin_type_repository = PluginTypeRepository()
        plugin_type_repository._plugin_types = {
            DummyPluginDefinition.type().id: DummyPluginDefinition,
        }
        mocker.patch(
            "betty.plugin.PluginTypeRepository", return_value=plugin_type_repository
        )
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert DummyPluginOne.plugin() in await sut.plugins(
            DummyPluginDefinition.type().id
        )
