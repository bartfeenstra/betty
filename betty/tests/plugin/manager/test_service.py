from collections.abc import Iterable

from pytest_mock import MockerFixture

from betty.app import App
from betty.plugin import PluginTypeRepository
from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.level import UNIVERSE
from betty.service.requirement.app import require_app
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne


class TestServiceLevelPluginManager:
    def test_types(self) -> None:
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert len(list(sut.types))

    async def test_plugins__with_plugin_type(self) -> None:
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert sut.plugins(DummyPluginDefinition) is sut.plugins(DummyPluginDefinition)
        assert (
            DummyPluginOne.plugin()
            in await sut.plugins(DummyPluginDefinition).plugins()
        )

    async def test_plugins__with_plugin_type_id(self, mocker: MockerFixture) -> None:
        plugin_type_repository = PluginTypeRepository()
        plugin_type_repository._plugin_types = {
            DummyPluginDefinition.type().id: DummyPluginDefinition,
        }
        mocker.patch(
            "betty.plugin.PluginTypeRepository", return_value=plugin_type_repository
        )
        sut = ServiceLevelPluginManager(UNIVERSE)
        assert (
            DummyPluginOne.plugin()
            in await sut.plugins(DummyPluginDefinition.type().id).plugins()
        )

    async def test_plugins__should_forward_services(self, isolated_app: App) -> None:
        async def _discovery(app: App) -> Iterable[DummyPluginDefinition]:
            assert app is isolated_app
            return ()

        sut = ServiceLevelPluginManager(isolated_app)
        with DummyPluginDefinition.type().discoverer.override(require_app(_discovery)):
            await sut.plugins(DummyPluginDefinition).plugins()

    async def test_plugins__with_overridden_discoveries(self) -> None:
        @DummyPluginDefinition("dummy-plugin-override")
        class _Plugin(DummyPlugin):
            pass

        sut = ServiceLevelPluginManager(UNIVERSE)
        with DummyPluginDefinition.type().discoverer.override(_Plugin):
            assert (
                _Plugin.plugin() in await sut.plugins(DummyPluginDefinition).plugins()
            )
        assert (
            _Plugin.plugin() not in await sut.plugins(DummyPluginDefinition).plugins()
        )
