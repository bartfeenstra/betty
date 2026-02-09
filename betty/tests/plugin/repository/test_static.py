import pytest

from betty.plugin.error import PluginNotFound
from betty.plugin.repository.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestStaticPluginRepository:
    async def test_get(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DummyPluginOne)
        assert await sut.plugin(DummyPluginOne.plugin().id) is DummyPluginOne.plugin()

    def test_get__not_found(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            sut.plugin(DummyPluginOne.plugin().id)

    async def test___aiter__(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DummyPluginOne)
        plugin = [plugin async for plugin in aiter(sut)][0]
        assert plugin is DummyPluginOne.plugin()

    async def test___aiter___without_plugins(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopIteration):
            await anext(aiter(sut))
