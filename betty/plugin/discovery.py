"""
Plugin discovery.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Mapping
from contextlib import suppress
from importlib import metadata
from typing import TYPE_CHECKING, Final, cast, final

from betty.asyncio import resolve_await
from betty.concurrent import ThreadSafeLock
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    resolve_plugin_definition,
    resolve_plugin_id,
)
from betty.requirement import UnmetRequirement
from betty.service_level import ServiceLevel
from betty.string import kebab_case_to_snake_case
from betty.threading import threadsafe

if TYPE_CHECKING:
    import builtins

    from betty.machine_name import MachineName


type ResolvableDiscovery[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    ResolvablePluginDefinition[PluginDefinitionT]
    | Callable[
        [ServiceLevel],
        Awaitable[Iterable[ResolvableDiscovery[PluginDefinitionT]]]
        | Iterable[ResolvableDiscovery[PluginDefinitionT]],
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
        for plugins in await gather(*[
            _discover(discovery, services) for discovery in discoveries
        ])
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


@final
@threadsafe
class PluginDiscoverer[PluginDefinitionT: PluginDefinition = PluginDefinition]:
    """
    Discover plugin definitions of a specific plugin type.
    """

    def __init__(
        self,
        services: ServiceLevel,
        plugin_type: builtins.type[PluginDefinitionT],
        plugin_overrides: Iterable[ResolvableDiscovery[PluginDefinition]] | None = None,
        /,
    ):
        self._services = services
        self.type: Final[type[PluginDefinitionT]] = plugin_type
        """
        The plugin type.
        """
        self._lock = ThreadSafeLock()
        self._discovery = (
            [self._discover] if plugin_overrides is None else plugin_overrides
        )
        self.__plugins: Mapping[MachineName, PluginDefinitionT] | None = None

    def _discover(
        self, services: ServiceLevel
    ) -> Iterable[ResolvableDiscovery[PluginDefinitionT]]:
        for entry_point in metadata.entry_points(
            group=f"betty.{kebab_case_to_snake_case(self.type.type().id)}"
        ):
            yield cast(ResolvableDiscovery[PluginDefinitionT], entry_point.load())

    async def _plugins(self) -> Mapping[MachineName, PluginDefinitionT]:
        if self.__plugins is not None:
            return self.__plugins
        async with self._lock:
            if self.__plugins is not None:
                return self.__plugins
            self.__plugins = {
                plugin.id: plugin
                for plugin in await discover(self._services, *self._discovery)
            }
            return self.__plugins

    async def __aiter__(self) -> AsyncIterator[PluginDefinitionT]:
        for plugin in (await self._plugins()).values():
            yield plugin

    async def get(self, key: ResolvablePluginId) -> PluginDefinitionT:
        """
        Get a plugin by its ID.
        """
        key = resolve_plugin_id(key)
        try:
            return (await self._plugins())[key]
        except KeyError:
            raise PluginNotFound(self.type, key, await self.ids()) from None

    def __getitem__(self, key: ResolvablePluginId) -> Awaitable[PluginDefinitionT]:
        return self.get(key)

    async def ids(self) -> Iterable[MachineName]:
        """
        Iterate over the IDs of the available plugins.
        """
        return (await self._plugins()).keys()
