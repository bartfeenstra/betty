from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest
from typing_extensions import TypeVar

from betty.plugin import PluginDefinition
from betty.plugin.discovery import (
    Discoverer,
    PluginDiscovery,
    ResolvableDiscovery,
    discover,
)
from betty.service.level import UNIVERSE
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Set

    from betty.service.level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class _StaticDiscovery(PluginDiscovery[_PluginDefinitionT]):
    def __init__(self, *discoveries: ResolvableDiscovery[_PluginDefinitionT]):
        self._discoveries = discoveries

    @override
    async def discover(
        self, services: ServiceLevel, /
    ) -> Iterable[ResolvableDiscovery[_PluginDefinitionT]]:
        return self._discoveries


class TestDiscoverer:
    async def _discover(self, sut: Discoverer):
        return list(await sut.discover(UNIVERSE))

    async def test_discover(self) -> None:
        sut = Discoverer([DummyPluginTwo])
        assert await self._discover(sut) == [DummyPluginTwo.plugin()]

    async def test_add(self) -> None:
        sut = Discoverer()
        sut.add(DummyPluginTwo)
        assert await self._discover(sut) == [DummyPluginTwo.plugin()]

    async def test_override(self) -> None:
        sut = Discoverer()
        assert not await self._discover(sut)
        with sut.override(DummyPluginTwo):
            assert await self._discover(sut) == [DummyPluginTwo.plugin()]
        assert not await self._discover(sut)

    async def test_add__during_override(self) -> None:
        sut = Discoverer()
        with sut.override(DummyPluginOne):
            sut.add(DummyPluginTwo)
            assert await self._discover(sut) == [DummyPluginOne.plugin()]
        assert await self._discover(sut) == [DummyPluginTwo.plugin()]

    def test_overridden(self) -> None:
        sut = Discoverer()
        assert not sut.overridden
        with sut.override():
            assert sut.overridden
        assert not sut.overridden


def _new_static_discovery_sync(
    *discoveries: ResolvableDiscovery[DummyPluginDefinition],
) -> Callable[[ServiceLevel], Iterable[ResolvableDiscovery[DummyPluginDefinition]]]:
    def _static_discovery_sync(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscovery[DummyPluginDefinition]]:
        return discoveries

    return _static_discovery_sync


def _new_static_discovery_async(
    *discoveries: ResolvableDiscovery[DummyPluginDefinition],
) -> Callable[
    [ServiceLevel],
    Awaitable[Iterable[ResolvableDiscovery[DummyPluginDefinition]]],
]:
    async def _static_discovery_async(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscovery[DummyPluginDefinition]]:
        return discoveries

    return _static_discovery_async


@pytest.mark.parametrize(
    ("expected", "discoveries"),
    [
        (set(), []),
        ({DummyPluginOne.plugin()}, [DummyPluginOne]),
        ({DummyPluginOne.plugin()}, [DummyPluginOne.plugin()]),
        ({DummyPluginOne.plugin()}, [_new_static_discovery_sync(DummyPluginOne)]),
        (
            {DummyPluginOne.plugin()},
            [_new_static_discovery_sync(DummyPluginOne.plugin())],
        ),
        ({DummyPluginOne.plugin()}, [_new_static_discovery_async(DummyPluginOne)]),
        (
            {DummyPluginOne.plugin()},
            [_new_static_discovery_async(DummyPluginOne.plugin())],
        ),
        ({DummyPluginOne.plugin()}, [_StaticDiscovery(DummyPluginOne)]),
        ({DummyPluginOne.plugin()}, [_StaticDiscovery(DummyPluginOne.plugin())]),
    ],
)
async def test_discover(
    expected: Set[DummyPluginDefinition],
    discoveries: Iterable[ResolvableDiscovery[DummyPluginDefinition]],
) -> None:
    assert set(await discover(UNIVERSE, *discoveries)) == expected
