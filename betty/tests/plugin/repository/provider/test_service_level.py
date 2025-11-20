from collections.abc import Iterable

from pytest_mock import MockerFixture

from betty.app import App
from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.app import AppDiscovery
from betty.plugin.repository.provider.service_level import (
    ServiceLevelPluginRepositoryProvider,
)
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE, DummyPluginDefinition


class TestServiceLevelPluginRepositoryProvider:
    async def test_plugins__with_plugin_type(self) -> None:
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert await sut.plugins(DummyPluginDefinition) is await sut.plugins(
            DummyPluginDefinition
        )
        assert DUMMY_PLUGIN_ONE in await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_plugin_type_id(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.plugin.plugin_types",
            return_value={
                DummyPluginDefinition.type.id: DummyPluginDefinition,
            },
        )
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert DUMMY_PLUGIN_ONE in await sut.plugins(DummyPluginDefinition.type.id)

    async def test_plugins__should_forward_service_level(
        self, temporary_app: App
    ) -> None:
        async def _discovery(app: App) -> Iterable["_PluginDefinition"]:
            assert app is temporary_app
            return ()

        class _PluginDefinition(PluginDefinition):
            type = PluginTypeDefinition(
                id="-",
                label=Plain(""),
                discoveries=AppDiscovery(_discovery),
            )

        sut = ServiceLevelPluginRepositoryProvider(temporary_app)
        await sut.plugins(_PluginDefinition)

    async def test_plugins__with_overridden_discoveries(self) -> None:
        plugin = DummyPluginDefinition(
            id="dummy-plugin-four",
        )
        sut = ServiceLevelPluginRepositoryProvider(None)
        with DummyPluginDefinition.type.override_discovery(plugin):
            assert plugin in await sut.plugins(DummyPluginDefinition)
        assert plugin not in await sut.plugins(DummyPluginDefinition)
