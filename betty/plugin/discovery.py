"""
Plugin discovery.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Awaitable, Callable, Iterable
from contextlib import suppress

from betty.asyncio import resolve_await
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.requirement import UnmetRequirement
from betty.service.level import ServiceLevel

type ResolvableDiscovery[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    ResolvablePluginDefinition[PluginDefinitionT]
    | Callable[
        [ServiceLevel],
        Awaitable[Iterable["ResolvableDiscovery[PluginDefinitionT]"]]
        | Iterable["ResolvableDiscovery[PluginDefinitionT]"],
    ]
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

    with suppress(ValueError):
        return [resolve_plugin_definition(discovery)]
    try:
        return await discover(services, *await resolve_await(discovery(services)))
    except UnmetRequirement:
        return ()
