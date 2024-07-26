import pytest

from betty.locale.localizable import Localizable, plain
from betty.plugin import Plugin, PluginNotFound
from betty.machine_id import MachineId
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository


class _ProxyPluginRepositoryTestPluginBase(Plugin):
    @classmethod
    def plugin_id(cls) -> MachineId:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("")  # pragma: no cover


class ProxyPluginRepositoryTestPluginOne(_ProxyPluginRepositoryTestPluginBase):
    pass  # pragma: no cover


class ProxyPluginRepositoryTestPluginTwo(_ProxyPluginRepositoryTestPluginBase):
    pass  # pragma: no cover


class ProxyPluginRepositoryTestPluginThree(_ProxyPluginRepositoryTestPluginBase):
    pass  # pragma: no cover


class TestProxyPluginRepository:
    async def test_get(self) -> None:
        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(ProxyPluginRepositoryTestPluginOne)
        )
        await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test_get_not_found_without_upstreams(self) -> None:
        sut = ProxyPluginRepository[Plugin]()
        with pytest.raises(PluginNotFound):
            await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test_get_not_found_with_upstreams(self) -> None:
        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(), StaticPluginRepository(), StaticPluginRepository()
        )
        with pytest.raises(PluginNotFound):
            await sut.get(ProxyPluginRepositoryTestPluginOne.plugin_id())

    async def test___aiter___without_upstreams(self) -> None:
        sut = ProxyPluginRepository[Plugin]()
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter___with_upstreams_without_plugins(self) -> None:
        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(), StaticPluginRepository(), StaticPluginRepository()
        )
        with pytest.raises(StopAsyncIteration):
            await anext(aiter(sut))

    async def test___aiter___with_upstreams_with_plugins(self) -> None:
        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(ProxyPluginRepositoryTestPluginOne),
            StaticPluginRepository(
                ProxyPluginRepositoryTestPluginTwo, ProxyPluginRepositoryTestPluginOne
            ),
            StaticPluginRepository(
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
