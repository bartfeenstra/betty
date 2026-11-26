"""
Plugin repositories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.concurrent import ThreadSafeLock
from betty.definition.discover import Discovery, discover
from betty.definition.id import ResolvableId, resolve_id
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound

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
        /,
        *,
        discovery: Discovery[DefinitionT] | None = None,
    ):
        self._services = services
        self.type: Final[type[DefinitionT]] = plugin_type
        """
        The plugin type.
        """
        self._lock = ThreadSafeLock()
        self._discoveries = [plugin_type.definition.discovery]
        if discovery:
            self._discoveries.append(discovery)
        self._plugins: Mapping[MachineName, DefinitionT] | None = None

    async def _get_plugins(self) -> Mapping[MachineName, DefinitionT]:
        if self._plugins is not None:
            return self._plugins
        async with self._lock:
            if self._plugins is not None:
                return self._plugins
            self._plugins = {
                plugin.id: plugin
                for plugin in await discover(self._services, *self._discoveries)
            }
            return self._plugins

    async def __aiter__(self) -> AsyncIterator[DefinitionT]:
        for plugin in (await self._get_plugins()).values():
            yield plugin

    async def get(self, key: ResolvableId) -> DefinitionT:
        """
        Get a plugin by its ID.
        """
        key = resolve_id(key)
        try:
            return (await self._get_plugins())[key]
        except KeyError:
            raise PluginNotFound(self.type, key, await self.ids()) from None

    def __getitem__(self, key: ResolvableId) -> Awaitable[DefinitionT]:
        return self.get(key)

    async def ids(self) -> Iterable[MachineName]:
        """
        Iterate over the IDs of the available plugins.
        """
        return (await self._get_plugins()).keys()
