import pytest

from betty.plugin import PluginNotFound
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE, DummyPluginDefinition


class TestStaticPluginRepository:
    async def test_get(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE)
        assert await sut.get(DUMMY_PLUGIN_ONE.id) is DUMMY_PLUGIN_ONE

    async def test_get_not_found(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            await sut.get(DUMMY_PLUGIN_ONE.id)

    async def test___aiter__(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE)
        plugin = [plugin async for plugin in sut][0]
        assert plugin is DUMMY_PLUGIN_ONE

    async def test___aiter___without_plugins(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))
