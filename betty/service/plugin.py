"""
Service plugin management.

Service levels can expose services of plugin instances.
"""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, Any, cast, final, overload, override

from betty.collection.keyed import KeyedCollection
from betty.concurrent import AsynchronizedLock
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import (
    Plugin,
    PluginDefinition,
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.error import PluginNotFound
from betty.string import kebab_case_to_snake_case
from betty.typing import threadsafe

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncIterator, Awaitable, Iterable, Iterator, Mapping

    from ty_extensions import Intersection

    from betty.service.level import ServiceLevel


@final
class PluginCollection[PluginDefinitionT: PluginDefinition, PluginT: Plugin](
    KeyedCollection[MachineName, ResolvablePluginId[PluginDefinitionT], PluginT]
):
    """
    A collection of plugin instances.
    """

    def __init__(self, plugins: Iterable[Iterable[PluginT]], /):
        self._batches = tuple(map(tuple, plugins))
        self._all = {
            plugin.plugin().id: plugin for batch in self._batches for plugin in batch
        }

    @override
    def __len__(self) -> int:
        return len(self._all)

    @override
    def __iter__(self) -> Iterator[PluginT]:
        yield from self._all.values()

    @override
    def __contains__(self, key: Any) -> bool:
        try:
            return resolve_plugin_id(key) in self._all
        except ValueError:
            return False

    @overload
    def __getitem__[T](
        self, key: type[Intersection[PluginT, T]]
    ) -> Intersection[PluginT, T]:
        pass

    @overload
    def __getitem__(self, key: ResolvablePluginId[PluginDefinitionT]) -> PluginT:
        pass

    @override
    def __getitem__(self, key):
        return self._all[resolve_plugin_id(key)]

    @override
    def keys(self) -> Iterable[MachineName]:
        return self._all.keys()


@final
@threadsafe
class PluginManager[PluginDefinitionT: PluginDefinition]:
    """
    Expose the plugin type definition and plugin definitions for a specific plugin type.
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
