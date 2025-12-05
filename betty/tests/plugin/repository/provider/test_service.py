from collections.abc import Iterable

from pytest_mock import MockerFixture

from betty.app import App
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.app import AppDiscovery
from betty.plugin.repository.provider.service import (
    ServiceLevelPluginRepositoryProvider,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne


class TestServiceLevelPluginRepositoryProvider:
    async def test_plugins__with_plugin_type(self) -> None:
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert await sut.plugins(DummyPluginDefinition) is await sut.plugins(
            DummyPluginDefinition
        )
        assert DummyPluginOne.plugin in await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_plugin_type_id(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.plugin.plugin_types",
            return_value={
                DummyPluginDefinition.type.id: DummyPluginDefinition,
            },
        )
        sut = ServiceLevelPluginRepositoryProvider(None)
        assert DummyPluginOne.plugin in await sut.plugins(DummyPluginDefinition.type.id)

    async def test_plugins__should_forward_services(self, isolated_app: App) -> None:
        async def _discovery(app: App) -> Iterable["_PluginDefinition"]:
            assert app is isolated_app
            return ()

        class _PluginDefinition(PluginDefinition):
            type = PluginTypeDefinition(
                "-",
                DUMMY_LOCALIZABLE,
                DUMMY_LOCALIZABLE,
                DUMMY_COUNTABLE_LOCALIZABLE,
                discoveries=AppDiscovery(_discovery),
            )

        sut = ServiceLevelPluginRepositoryProvider(isolated_app)
        await sut.plugins(_PluginDefinition)

    async def test_plugins__with_overridden_discoveries(self) -> None:
        @DummyPluginDefinition("dummy-plugin-override")
        class _Plugin(DummyPlugin):
            pass

        sut = ServiceLevelPluginRepositoryProvider(None)
        with DummyPluginDefinition.type.override_discovery(_Plugin.plugin):
            assert _Plugin.plugin in await sut.plugins(DummyPluginDefinition)
        assert _Plugin.plugin not in await sut.plugins(DummyPluginDefinition)
