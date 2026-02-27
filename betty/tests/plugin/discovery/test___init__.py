from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.plugin import PluginDefinition
from betty.plugin.discovery import ResolvableDiscovery, discover
from betty.service.level import UNIVERSE
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Set

    from betty.service.level import ServiceLevel


class _StaticDiscovery[PluginDefinitionT: PluginDefinition]:
    def __init__(self, *discoveries: ResolvableDiscovery[PluginDefinitionT]):
        self._discoveries = discoveries

    async def __call__(
        self, services: ServiceLevel, /
    ) -> Iterable[ResolvableDiscovery[PluginDefinitionT]]:
        return self._discoveries


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
