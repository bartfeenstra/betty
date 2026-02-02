from collections.abc import Iterable

from betty.app import App
from betty.service.level import universe
from betty.service.plugin import PluginManager
from betty.service.requirement.app import require_app
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne


class TestServiceLevelPluginManager:
    def test_types(self) -> None:
        sut = PluginManager(universe)
        assert len(list(sut.types))

    async def test_plugins__with_plugin_type(self) -> None:
        sut = PluginManager(universe)
        assert await sut.plugins(DummyPluginDefinition) is await sut.plugins(
            DummyPluginDefinition
        )
        assert DummyPluginOne.plugin() in await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_plugin_type_id(self) -> None:
        sut = PluginManager(universe)
        assert sut.types

    async def test_plugins__should_forward_services(self, isolated_app: App) -> None:
        async def _discovery(*, app: App) -> Iterable[DummyPluginDefinition]:
            assert app is isolated_app
            return ()

        sut = PluginManager(isolated_app)
        with DummyPluginDefinition.type().discoverer.override(require_app(_discovery)):
            await sut.plugins(DummyPluginDefinition)

    async def test_plugins__with_overridden_discoveries(self) -> None:
        @DummyPluginDefinition("dummy-plugin-override")
        class _Plugin(DummyPlugin):
            pass

        sut = PluginManager(universe)
        with DummyPluginDefinition.type().discoverer.override(_Plugin):
            assert _Plugin.plugin() in await sut.plugins(DummyPluginDefinition)
        assert _Plugin.plugin() not in await sut.plugins(DummyPluginDefinition)
