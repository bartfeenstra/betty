import pytest

from betty.locale.localizable import Localizable, plain
from betty.plugin import Plugin, PluginNotFound, PluginId
from betty.plugin.static import StaticPluginRepository


class StaticPluginRepositoryTestPlugin(Plugin):
    @classmethod
    def plugin_id(cls) -> PluginId:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("")  # pragma: no cover


class TestStaticPluginRepository:
    async def test_get(self) -> None:
        sut = StaticPluginRepository[Plugin](StaticPluginRepositoryTestPlugin)
        await sut.get(StaticPluginRepositoryTestPlugin.plugin_id())

    async def test_get_not_found(self) -> None:
        sut = StaticPluginRepository[Plugin]()
        with pytest.raises(PluginNotFound):
            await sut.get(StaticPluginRepositoryTestPlugin.plugin_id())

    async def test___aiter__(self) -> None:
        sut = StaticPluginRepository[Plugin](StaticPluginRepositoryTestPlugin)
        plugin = await anext(aiter(sut))
        assert plugin is StaticPluginRepositoryTestPlugin

    async def test___aiter___without_plugins(self) -> None:
        sut = StaticPluginRepository[Plugin]()
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))
