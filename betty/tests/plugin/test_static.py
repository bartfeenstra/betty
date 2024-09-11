import pytest

from betty.locale.localizable import Localizable, static
from betty.plugin import Plugin, PluginNotFound
from betty.machine_name import MachineName
from betty.plugin.static import StaticPluginRepository


class StaticPluginRepositoryTestPlugin(Plugin):
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return static("")  # pragma: no cover


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
        plugin = [plugin async for plugin in sut][0]
        assert plugin is StaticPluginRepositoryTestPlugin

    async def test___aiter___without_plugins(self) -> None:
        sut = StaticPluginRepository[Plugin]()
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))
