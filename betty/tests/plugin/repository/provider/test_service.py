from collections.abc import Iterable

from pytest_mock import MockerFixture

from betty.app import App
from betty.plugin import PluginTypeRepository
from betty.plugin.discovery.app import AppDiscovery
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.repository.provider.service import (
    ServiceLevelPluginRepositoryProvider,
)
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne


class TestServiceLevelPluginRepositoryProvider:
    async def test_plugins__with_plugin_type(self) -> None:
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert await sut.plugins(DummyPluginDefinition) is await sut.plugins(
            DummyPluginDefinition
        )
        assert DummyPluginOne.plugin() in await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_plugin_type_id(self, mocker: MockerFixture) -> None:
        plugin_type_repository = PluginTypeRepository()
        plugin_type_repository._plugin_types = {
            DummyPluginDefinition.type().id: DummyPluginDefinition,
        }
        mocker.patch("betty.plugin.plugin_types", new=plugin_type_repository)
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert DummyPluginOne.plugin() in await sut.plugins(
            DummyPluginDefinition.type().id
        )

    async def test_plugins__should_forward_services(self, isolated_app: App) -> None:
        async def _discovery(app: App) -> Iterable[DummyPluginDefinition]:
            assert app is isolated_app
            return ()

        sut = ServiceLevelPluginRepositoryProvider(isolated_app)
        with DummyPluginDefinition.type().override_discovery(AppDiscovery(_discovery)):
            await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_overridden_discoveries(self) -> None:
        @DummyPluginDefinition("dummy-plugin-override")
        class _Plugin(DummyPlugin):
            pass

        sut = ServiceLevelPluginRepositoryProvider(None)
        with DummyPluginDefinition.type().override_discovery(StaticDiscovery(_Plugin)):
            assert _Plugin.plugin() in await sut.plugins(DummyPluginDefinition)
        assert _Plugin.plugin() not in await sut.plugins(DummyPluginDefinition)
