from typing import TypeVar

import pytest

from betty.factory import FactoryError
from betty.plugin import Plugin, PluginNotFound, PluginIdentifier
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

    @pytest.mark.parametrize(
        "target",
        [
            ProxyPluginRepositoryTestPluginOne,
            ProxyPluginRepositoryTestPluginOne.plugin_id(),
        ],
    )
    async def test_new_target_with_own_factory(
        self, target: PluginIdentifier[Plugin]
    ) -> None:
        async def _error_raising_factory(cls: type[_T]) -> _T:
            raise FactoryError(cls)

        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(
                ProxyPluginRepositoryTestPluginOne, factory=_error_raising_factory
            )
        )
        await sut.new_target(target)

    @pytest.mark.parametrize(
        "target",
        [
            ProxyPluginRepositoryTestPluginOne,
            ProxyPluginRepositoryTestPluginOne.plugin_id(),
        ],
    )
    async def test_new_target_with_upstream_factory(
        self, target: PluginIdentifier[Plugin]
    ) -> None:
        async def _error_raising_factory(cls: type[_T]) -> _T:
            raise FactoryError(cls)

        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(ProxyPluginRepositoryTestPluginOne),
            factory=_error_raising_factory,
        )
        await sut.new_target(target)

    @pytest.mark.parametrize(
        "target",
        [
            ProxyPluginRepositoryTestPluginOne,
            ProxyPluginRepositoryTestPluginOne.plugin_id(),
        ],
    )
    async def test_new_target_without_successful_factories(
        self, target: PluginIdentifier[Plugin]
    ) -> None:
        async def _error_raising_factory(cls: type[_T]) -> _T:
            raise FactoryError(cls)

        sut = ProxyPluginRepository[Plugin](
            StaticPluginRepository(
                ProxyPluginRepositoryTestPluginOne, factory=_error_raising_factory
            ),
            factory=_error_raising_factory,
        )
        with pytest.raises(FactoryError):
            await sut.new_target(ProxyPluginRepositoryTestPluginOne)
