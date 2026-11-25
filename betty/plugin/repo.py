"""
Plugin repositories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.concurrent import ThreadSafeLock
from betty.definition.id import ResolvableId, resolve_id
from betty.discover import ResolvableDiscoverer, discover
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.string import kebab_case_to_snake_case

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Iterable, Mapping

    from betty.machine_name import MachineName
    from betty.service_level import ServiceLevel


@final
class PluginRepository[DefinitionT: PluginDefinition = PluginDefinition]:
    """
    Discover plugin definitions of a specific plugin type.
    """

    def __init__(
        self,
        services: ServiceLevel,
        plugin_type: type[DefinitionT],
        plugin_overrides: Iterable[ResolvableDiscoverer[PluginDefinition]]
        | None = None,
        /,
    ):
        from betty.discoverers.entry_point import EntryPointDiscovery

        self._services = services
        self.type: Final[type[DefinitionT]] = plugin_type
        """
        The plugin type.
        """
        self._lock = ThreadSafeLock()
        self._discovery = (
            [
                EntryPointDiscovery(
                    plugin_type, kebab_case_to_snake_case(plugin_type.definition.id)
                )
            ]
            if plugin_overrides is None
            else plugin_overrides
        )
        self.__plugins: Mapping[MachineName, DefinitionT] | None = None

    async def _plugins(self) -> Mapping[MachineName, DefinitionT]:
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

    async def __aiter__(self) -> AsyncIterator[DefinitionT]:
        for plugin in (await self._plugins()).values():
            yield plugin

    async def get(self, key: ResolvableId) -> DefinitionT:
        """
        Get a plugin by its ID.
        """
        key = resolve_id(key)
        try:
            return (await self._plugins())[key]
        except KeyError:
            raise PluginNotFound(self.type, key, await self.ids()) from None

    def __getitem__(self, key: ResolvableId) -> Awaitable[DefinitionT]:
        return self.get(key)

    async def ids(self) -> Iterable[MachineName]:
        """
        Iterate over the IDs of the available plugins.
        """
        return (await self._plugins()).keys()
