"""
Plugin discovery services.
"""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, cast, final

from betty.concurrent import AsynchronizedLock
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.error import PluginNotFound
from betty.string import kebab_case_to_snake_case
from betty.typing import threadsafe

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncIterator, Awaitable, Iterable, Mapping

    from betty.service.level import ServiceLevel


@final
@threadsafe
class PluginDiscoverer[PluginDefinitionT: PluginDefinition]:
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
        self._type = plugin_type
        self._lock = AsynchronizedLock.new_threadsafe()
        self._discovery = (
            [self._discover] if plugin_overrides is None else plugin_overrides
        )
        self.__plugins: Mapping[MachineName, PluginDefinitionT] | None = None

    @property
    def type(self) -> builtins.type[PluginDefinitionT]:
        """
        The plugin type.
        """
        return self._type

    def _discover(
        self, services: ServiceLevel
    ) -> Iterable[ResolvableDiscovery[PluginDefinitionT]]:
        for entry_point in metadata.entry_points(
            group=f"betty.{kebab_case_to_snake_case(self.type.type().id)}"
        ):
            yield cast(ResolvableDiscovery[PluginDefinitionT], entry_point.load())

    async def _plugins(self) -> Mapping[MachineName, PluginDefinitionT]:
        from betty.plugin.discovery import discover

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

    async def _get(self, key: ResolvableMachineName) -> PluginDefinitionT:
        key = MachineName.resolve(key)
        try:
            return (await self._plugins())[key]
        except KeyError:
            raise PluginNotFound(self._type, key, await self.ids()) from None

    def __getitem__(self, key: ResolvableMachineName) -> Awaitable[PluginDefinitionT]:
        return self._get(key)

    async def ids(self) -> Iterable[MachineName]:
        """
        Iterate over the IDs of the available plugins.
        """
        return (await self._plugins()).keys()
