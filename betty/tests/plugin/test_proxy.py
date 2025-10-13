import pytest

from betty.plugin import PluginNotFound
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)


class TestProxyPluginRepository:
    async def test_get(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
        )
        assert await sut.get(DUMMY_PLUGIN_ONE.id) is DUMMY_PLUGIN_ONE

    async def test_get__not_found_without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            await sut.get(DUMMY_PLUGIN_ONE.id)

    async def test_get__not_found_with_upstreams(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_TWO),
        )
        with pytest.raises(PluginNotFound):
            await sut.get(DUMMY_PLUGIN_THREE.id)

    async def test___aiter____without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter____with_upstreams_without_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition),
            StaticPluginRepository(DummyPluginDefinition),
            StaticPluginRepository(DummyPluginDefinition),
        )
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter____with_upstreams_with_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
            StaticPluginRepository(
                DummyPluginDefinition,
                DUMMY_PLUGIN_TWO,
                DUMMY_PLUGIN_ONE,
            ),
            StaticPluginRepository(
                DummyPluginDefinition,
                DUMMY_PLUGIN_THREE,
                DUMMY_PLUGIN_TWO,
                DUMMY_PLUGIN_ONE,
            ),
        )
        actual = [plugin async for plugin in aiter(sut)]
        assert actual == [
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        ]
