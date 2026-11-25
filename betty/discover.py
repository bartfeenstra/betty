"""
Definition discovery.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Callable, Iterable
from contextlib import suppress

from betty.asyncio import ResolvableAwaitable, resolve_await
from betty.definition import Definition, ResolvableDefinition, resolve_definition
from betty.requirement import UnmetRequirement
from betty.service_level import ServiceLevel

type ResolvableDiscoverer[DefinitionT: Definition = Definition] = (
    ResolvableDefinition[DefinitionT]
    | Callable[
        [ServiceLevel],
        ResolvableAwaitable[Iterable[ResolvableDiscoverer[DefinitionT]]],
    ]
)


async def discover[DefinitionT: Definition](
    services: ServiceLevel, *discoverers: ResolvableDiscoverer[DefinitionT]
) -> Iterable[DefinitionT]:
    """
    Discover definitions.
    """
    return [
        definition
        for definitions in await gather(*[
            _discover(discoverer, services) for discoverer in discoverers
        ])
        for definition in definitions
    ]


async def _discover[DefinitionT: Definition](
    discoverer: ResolvableDiscoverer[DefinitionT], services: ServiceLevel
) -> Iterable[DefinitionT]:
    with suppress(ValueError):
        return [resolve_definition(discoverer)]
    try:
        return await discover(
            services,
            *await resolve_await(
                discoverer(
                    services,  # ty: ignore[too-many-positional-arguments]
                )  # ty: ignore[call-non-callable]
            ),
        )
    except UnmetRequirement:
        return ()
