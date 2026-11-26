from __future__ import annotations

from typing import TYPE_CHECKING, Never

import pytest

from betty.definition.discover import Discovery, discover
from betty.requirement import UnmetRequirement
from betty.service_level import ServiceLevel
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Set


def _new_static_discovery_sync(
    *discoveries: Discovery[DummyPluginDefinition],
) -> Callable[[ServiceLevel], Discovery[DummyPluginDefinition]]:
    def _static_discovery_sync(
        services: ServiceLevel,
    ) -> Discovery[DummyPluginDefinition]:
        return discoveries

    return _static_discovery_sync


def _new_static_discovery_async(
    *discoveries: Discovery[DummyPluginDefinition],
) -> Callable[[ServiceLevel], Awaitable[Discovery[DummyPluginDefinition]]]:
    async def _static_discovery_async(
        services: ServiceLevel,
    ) -> Discovery[DummyPluginDefinition]:
        return discoveries

    return _static_discovery_async


def _raises_unmet_requirement(services: ServiceLevel, /) -> Never:
    raise UnmetRequirement("Oops!")


@pytest.mark.parametrize(
    ("expected", "discoveries"),
    [
        # No discoveries.
        (set(), []),
        # Sequences.
        (
            {DummyPluginOne.definition, DummyPluginTwo.definition},
            [[DummyPluginOne.definition], (DummyPluginTwo.definition,)],
        ),
        # Definition instances.
        ({DummyPluginOne.definition}, [DummyPluginOne.definition]),
        # HasDefinition instances.
        ({DummyPluginOne.definition}, [DummyPluginOne]),
        # Sync callables.
        ({DummyPluginOne.definition}, [_new_static_discovery_sync(DummyPluginOne)]),
        # Async callables.
        ({DummyPluginOne.definition}, [_new_static_discovery_async(DummyPluginOne)]),
        # Callables that raise UnmetRequirement.
        (set(), [_raises_unmet_requirement]),
    ],
)
async def test_discover(
    expected: Set[DummyPluginDefinition],
    discoveries: Iterable[Discovery[DummyPluginDefinition]],
) -> None:
    assert set(await discover(ServiceLevel(), *discoveries)) == expected
