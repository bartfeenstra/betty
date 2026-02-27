"""
Plugin discovery.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Awaitable, Callable, Iterable

from betty.asyncio import resolve_await
from betty.plugin import Plugin, PluginDefinition, ResolvableDefinition
from betty.service.level import ServiceLevel

type ResolvableDiscovery[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    Callable[
        [ServiceLevel],
        Awaitable[Iterable["ResolvableDiscovery[PluginDefinitionT]"]]
        | Iterable["ResolvableDiscovery[PluginDefinitionT]"],
    ]
    | ResolvableDefinition[PluginDefinitionT]
)


async def discover[PluginDefinitionT: PluginDefinition](
    services: ServiceLevel, *discoveries: ResolvableDiscovery[PluginDefinitionT]
) -> Iterable[PluginDefinitionT]:
    """
    Discover plugins definitions.
    """
    return [
        plugin
        for plugins in await gather(
            *[_discover(discovery, services) for discovery in discoveries]
        )
        for plugin in plugins
    ]


async def _discover[PluginDefinitionT: PluginDefinition](
    discovery: ResolvableDiscovery[PluginDefinitionT], services: ServiceLevel
) -> Iterable[PluginDefinitionT]:
    from betty.service.requirement import UnmetRequirement

    try:
        if isinstance(discovery, PluginDefinition):
            return [discovery]  # ty:ignore[invalid-return-type]
        if isinstance(discovery, type) and issubclass(discovery, Plugin):
            return [discovery.plugin()]  # ty:ignore[invalid-argument-type,invalid-return-type]
        return await discover(services, *await resolve_await(discovery(services)))
    except UnmetRequirement:
        return ()
