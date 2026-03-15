"""
Service plugin management.

Service levels can expose services of plugin instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather
from collections import defaultdict
from contextlib import suppress
from graphlib import TopologicalSorter
from importlib import metadata
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
    final,
    overload,
    override,
)

from betty.collection.keyed import KeyedCollection
from betty.concurrent import AsynchronizedLock
from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import (
    Plugin,
    PluginDefinition,
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.error import PluginNotFound
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service.provider import service
from betty.string import kebab_case_to_snake_case
from betty.typing import threadsafe

if TYPE_CHECKING:
    import builtins
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )

    from ty_extensions import Intersection

    from betty.plugin.factory import PluginManufacturer
    from betty.service.level import ServiceLevel


@final
class PluginCollection[
    PluginDefinitionT: PluginDefinition = PluginDefinition,
    PluginT: Plugin = Plugin,
](KeyedCollection[MachineName, ResolvablePluginId[PluginDefinitionT], PluginT]):
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


class ServicePluginDefinition[BaseClsT = Any](PluginDefinition[BaseClsT]):
    """
    A definition of a service plugin.

    Service plugins are plugins of which instances may be exposed as services by service providers, and/or require other
    service plugins.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *args: Any,
        auto: bool = False,
        requires: Requires | None = None,
        **kwargs: Any,
    ):
        super().__init__(plugin_id, *args, **kwargs)
        self._auto = auto
        self._requires: Mapping[
            type[ServicePluginDefinition], Sequence[MachineName]
        ] = (
            {}
            if requires is None
            else {
                plugin_type: self.__resolve_plugin_id_sequence(plugin_type_requires)
                for plugin_type, plugin_type_requires in requires.items()
            }
        )

    def __resolve_plugin_id_sequence(
        self, plugin_ids: ResolvablePluginId | Iterable[ResolvablePluginId]
    ) -> Sequence[MachineName]:
        with suppress(ValueError):
            return [resolve_plugin_id(plugin_ids)]
        return list(map(resolve_plugin_id, plugin_ids))

    @property
    def auto(self) -> bool:
        """
        Whether to enable this plugin automatically.
        """
        return self._auto

    @property
    def requires(
        self,
    ) -> Mapping[type[ServicePluginDefinition], Sequence[MachineName]]:
        """
        Any service level plugins required by this plugin.
        """
        return self._requires


type Requires = Mapping[
    type[ServicePluginDefinition],
    ResolvablePluginId[ServicePluginDefinition]
    | Iterable[ResolvablePluginId[ServicePluginDefinition]],
]

type ServicePluginManufacturers = Mapping[
    type[ServicePluginDefinition],
    Iterable[
        PluginManufacturer[ServicePluginDefinition, Plugin[ServicePluginDefinition]]
    ],
]


@final
class ServicePluginManager(ManagedLifeCycle):
    """
    The service plugin manager.
    """

    def __init__(
        self,
        service_plugin_manufacturers: ServicePluginManufacturers | None,
        *,
        services: ServiceLevel,
    ):
        super().__init__()
        self._service_plugin_manufacturers = (
            {}
            if service_plugin_manufacturers is None
            else {
                plugin_type: {plugin.plugin_id: plugin for plugin in plugins}
                for plugin_type, plugins in service_plugin_manufacturers.items()
            }
        )
        self._service_plugins = {}
        self._services = services
        self.life_cycle.on_bootstrap(self._bootstrap)

    async def _bootstrap(self) -> None:
        sorter = TopologicalSorter[tuple[type[ServicePluginDefinition], MachineName]]()
        for (
            plugin_type,
            requested_plugins,
        ) in self._service_plugin_manufacturers.items():
            auto_plugins = {
                plugin.id
                async for plugin in self._services.plugins[plugin_type]
                if plugin.auto
            }
            for plugin in {*requested_plugins, *auto_plugins}:
                await self._expand_requires(sorter, plugin_type, plugin)
        sorter.prepare()
        service_plugins = defaultdict(list)
        while sorter.is_active():
            for plugin in await gather(
                *map(self._bootstrap_plugin, sorter.get_ready())
            ):
                plugin_type = type(plugin.plugin())
                service_plugins[plugin_type].append(plugin)
                sorter.done((plugin_type, plugin.plugin().id))
        plugin_types = set(self._service_plugin_manufacturers) | set(service_plugins)
        for plugin_type in plugin_types:
            self._service_plugins[plugin_type] = await self._new_plugin_collection(
                plugin_type, service_plugins[plugin_type]
            )

    async def _new_plugin_collection[ServicePluginDefinitionT: ServicePluginDefinition](
        self,
        plugin_type: type[ServicePluginDefinitionT],
        plugins: Iterable[Plugin[ServicePluginDefinitionT]],
    ) -> PluginCollection:
        plugins = sorted(plugins, key=lambda plugin: plugin.plugin().id)
        if issubclass(plugin_type, OrderedPluginDefinition):
            plugin_ids = {plugin.plugin().id for plugin in plugins}
            sorter = TopologicalSorter[MachineName]()
            for plugin in sorted(plugins, key=lambda plugin: plugin.plugin().id):
                plugin_definition = plugin.plugin()
                assert isinstance(plugin_definition, OrderedPluginDefinition)
                sorter.add(plugin_definition.id)
                for after in filter(plugin_definition.after, plugin_ids):
                    sorter.add(plugin_definition.id, after)
                for before in filter(plugin_definition.before, plugin_ids):
                    sorter.add(before, plugin_definition.id)
            sorter.prepare()
            sorted_plugins = []
            plugins_by_id = {plugin.plugin().id: plugin for plugin in plugins}
            while sorter.is_active():
                batch_plugin_ids = sorter.get_ready()
                sorted_plugins.append(
                    [plugins_by_id[plugin_id] for plugin_id in batch_plugin_ids]
                )
                sorter.done(*batch_plugin_ids)
            return PluginCollection(sorted_plugins)
        return PluginCollection([plugins])

    async def _bootstrap_plugin(
        self, plugin_type_and_id: tuple[type[ServicePluginDefinition], MachineName]
    ) -> Plugin:
        plugin = await self._new_plugin(plugin_type_and_id)
        if isinstance(plugin, LifeCycle):
            await plugin.bootstrap()
            self.life_cycle.attach(plugin)
        return plugin

    async def _new_plugin(
        self, plugin_type_and_id: tuple[type[ServicePluginDefinition], MachineName]
    ) -> Plugin:
        plugin_type, plugin_id = plugin_type_and_id
        try:
            manufacturer = self._service_plugin_manufacturers[plugin_type][plugin_id]
        except KeyError:
            return await self._services.factory.new(
                (await self._services.plugins[plugin_type][plugin_id]).cls
            )
        return await manufacturer(self._services)

    async def _expand_requires(
        self,
        sorter: TopologicalSorter[tuple[type[ServicePluginDefinition], MachineName]],
        plugin_type: type[ServicePluginDefinition],
        origin: MachineName,
    ) -> None:
        plugin = await self._services.plugins[plugin_type][origin]
        predecessors = set()
        for requires_plugin_type, requires_plugins in plugin.requires.items():
            for requires_plugin in requires_plugins:
                predecessors.add((requires_plugin_type, requires_plugin))
                await self._expand_requires(
                    sorter, requires_plugin_type, requires_plugin
                )
        sorter.add((plugin_type, origin), *predecessors)

    def __getitem__[ServicePluginDefinitionT: ServicePluginDefinition, PluginT: Plugin](
        self,
        plugin_type: type[
            Intersection[ServicePluginDefinitionT, PluginDefinition[PluginT]]
        ]
        | str,
        /,
    ) -> PluginCollection[ServicePluginDefinitionT, PluginT]:
        if isinstance(plugin_type, str):
            plugin_type = self._services.plugins[plugin_type].type
        return self._service_plugins[plugin_type]

    def __iter__(self) -> Iterator[type[ServicePluginDefinition]]:
        return iter(self._service_plugins)


class ServicePluginProvider(ManagedLifeCycle, ABC):
    """
    A service plugin provider.
    """

    @service
    @abstractmethod
    async def service_plugins(self) -> ServicePluginManager:
        """
        The service plugins.
        """
