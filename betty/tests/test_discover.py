from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.discover import ResolvableDiscoverer, discover
from betty.service_level import ServiceLevel
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Set


def _new_static_discovery_sync(
    *discoverers: ResolvableDiscoverer[DummyPluginDefinition],
) -> Callable[[ServiceLevel], Iterable[ResolvableDiscoverer[DummyPluginDefinition]]]:
    def _static_discovery_sync(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscoverer[DummyPluginDefinition]]:
        return discoverers

    return _static_discovery_sync


def _new_static_discovery_async(
    *discoverers: ResolvableDiscoverer[DummyPluginDefinition],
) -> Callable[
    [ServiceLevel],
    Awaitable[Iterable[ResolvableDiscoverer[DummyPluginDefinition]]],
]:
    async def _static_discovery_async(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscoverer[DummyPluginDefinition]]:
        return discoverers

    return _static_discovery_async


@pytest.mark.parametrize(
    ("expected", "discoverers"),
    [
        (set(), []),
        ({DummyPluginOne.definition}, [DummyPluginOne]),
        ({DummyPluginOne.definition}, [DummyPluginOne.definition]),
        ({DummyPluginOne.definition}, [_new_static_discovery_sync(DummyPluginOne)]),
        (
            {DummyPluginOne.definition},
            [_new_static_discovery_sync(DummyPluginOne.definition)],
        ),
        ({DummyPluginOne.definition}, [_new_static_discovery_async(DummyPluginOne)]),
        (
            {DummyPluginOne.definition},
            [_new_static_discovery_async(DummyPluginOne.definition)],
        ),
    ],
)
async def test_discover(
    expected: Set[DummyPluginDefinition],
    discoverers: Iterable[ResolvableDiscoverer[DummyPluginDefinition]],
) -> None:
    assert set(await discover(ServiceLevel(), *discoverers)) == expected
