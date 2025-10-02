from typing import TypeVar

import pytest

from betty.plugin import PluginNotFound
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPlugin

_T = TypeVar("_T")


class ProxyPluginRepositoryTestPluginOne(DummyPlugin):
    pass  # pragma: no cover


class ProxyPluginRepositoryTestPluginTwo(DummyPlugin):
    pass  # pragma: no cover


class ProxyPluginRepositoryTestPluginThree(DummyPlugin):
    pass  # pragma: no cover


class TestProxyPluginRepository:
    async def test_get(self) -> None:
        sut = ProxyPluginRepository(
            DummyPlugin,
            StaticPluginRepository(DummyPlugin, ProxyPluginRepositoryTestPluginOne),
        )
        await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test_get__not_found_without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPlugin)
        with pytest.raises(PluginNotFound):
            await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test_get__not_found_with_upstreams(self) -> None:
        sut = ProxyPluginRepository(
            DummyPlugin,
            StaticPluginRepository(DummyPlugin),
            StaticPluginRepository(DummyPlugin),
            StaticPluginRepository(DummyPlugin),
        )
        with pytest.raises(PluginNotFound):
            await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test___aiter____without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPlugin)
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter____with_upstreams_without_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPlugin,
            StaticPluginRepository(DummyPlugin),
            StaticPluginRepository(DummyPlugin),
            StaticPluginRepository(DummyPlugin),
        )
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter____with_upstreams_with_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPlugin,
            StaticPluginRepository(DummyPlugin, ProxyPluginRepositoryTestPluginOne),
            StaticPluginRepository(
                DummyPlugin,
                ProxyPluginRepositoryTestPluginTwo,
                ProxyPluginRepositoryTestPluginOne,
            ),
            StaticPluginRepository(
                DummyPlugin,
                ProxyPluginRepositoryTestPluginThree,
                ProxyPluginRepositoryTestPluginTwo,
                ProxyPluginRepositoryTestPluginOne,
            ),
        )
        actual = [plugin async for plugin in aiter(sut)]
        assert actual == [
            ProxyPluginRepositoryTestPluginOne,
            ProxyPluginRepositoryTestPluginTwo,
            ProxyPluginRepositoryTestPluginThree,
        ]
