"""
Service plugin management.

Service levels can expose services of plugin instances.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.collection.keyed import KeyedCollection
from betty.importlib import fully_qualified_name
from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import OrderedPluginDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.requirement import ServicePluginRequirement, UnmetRequirement
from betty.service.provider import ServiceProvider, service

if TYPE_CHECKING:
    from collections.abc import (
        Collection,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )

    from betty.service.level import ServiceLevel
    from betty.typing import Intersection


@final
class ServicePluginCollection[
    PluginDefinitionT: ServicePluginDefinition = ServicePluginDefinition,
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
    def keys(self) -> Sequence[MachineName]:
        return tuple(self._all.keys())


class ServicePluginDefinition[BaseClsT = Any](PluginClsDefinition[BaseClsT]):
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
        **kwargs: Any,
    ):
        super().__init__(plugin_id, *args, **kwargs)
        self._auto = auto

    @property
    def auto(self) -> bool:
        """
        Whether to enable this plugin automatically.
        """
        return self._auto


type ServicePluginTypes[
    PluginDefinitionT: ServicePluginDefinition = ServicePluginDefinition
] = Collection[type[PluginDefinitionT]]
type _Plugins[PluginDefinitionT: PluginClsDefinition = PluginClsDefinition] = Iterable[
    PluginManufacturer[PluginDefinitionT, Plugin[PluginDefinitionT]]
    | type[Plugin[PluginDefinitionT]]
]
type ServicePlugins[
    PluginDefinitionT: ServicePluginDefinition = ServicePluginDefinition
] = _Plugins[PluginDefinitionT]
type SupportPlugins = _Plugins


@final
class ServicePluginManager(ManagedLifeCycle):
    """
    The service plugin manager.
    """

    def __init__[ServicePluginTypesT: ServicePluginDefinition](
        self,
        services: ServiceLevel,
        service_plugin_types: ServicePluginTypes[ServicePluginTypesT],
        service_plugins: ServicePlugins[ServicePluginTypesT] = (),
        support_plugins: SupportPlugins = (),
        /,
    ):
        super().__init__()
        self._service_plugin_types = service_plugin_types
        self._service_plugin_manufacturers = self._map_plugins(service_plugins)
        self._support_plugins = self._map_plugins(support_plugins)
        self._service_plugins = {}
        self._services = services
        self.life_cycle.on_bootstrap(self._bootstrap)

    def _map_plugins(self, plugins: _Plugins) -> Mapping:
        plugin_map = defaultdict(dict)
        for plugin in plugins:
            if isinstance(plugin, PluginManufacturer):
                (plugin_map[plugin.plugin_type()][plugin.plugin_id]) = plugin
            else:
                (plugin_map[type(plugin.plugin())][plugin.plugin().id]) = plugin
        return plugin_map

    async def _bootstrap(self) -> None:
        sorter = TopologicalSorter[tuple[type[ServicePluginDefinition], MachineName]]()
        for (
            service_plugin_type,
            service_plugin_manufacturers,
        ) in self._service_plugin_manufacturers.items():
            for service_plugin_id in service_plugin_manufacturers:
                if service_plugin_type not in self._service_plugin_types:
                    raise UnmetRequirement(
                        f"{fully_qualified_name(service_plugin_type)} is not a service plugin type on {fully_qualified_name(type(self._services))}."
                    )
                await self._expand_requires(
                    sorter, service_plugin_type, service_plugin_id, True
                )
        for supported_plugin_type in self._support_plugins:
            for supported_plugin_id in self._support_plugins[supported_plugin_type]:
                await self._expand_requires(
                    sorter, supported_plugin_type, supported_plugin_id, False
                )
        for service_plugin_type in self._service_plugin_types:
            async for plugin in self._services.plugins[service_plugin_type]:
                if plugin.auto:
                    await self._expand_requires(sorter, type(plugin), plugin.id, True)
        sorter.prepare()
        service_plugins = {
            service_plugin_type: []
            for service_plugin_type in self._service_plugin_types
        }
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
    ) -> ServicePluginCollection:
        plugins = sorted(plugins, key=lambda plugin: plugin.plugin().id)
        if issubclass(plugin_type, OrderedPluginDefinition):
            plugin_ids = {plugin.plugin().id for plugin in plugins}
            sorter = TopologicalSorter[MachineName]()
            for plugin in sorted(plugins, key=lambda plugin: plugin.plugin().id):
                plugin_definition = plugin.plugin()
                assert isinstance(plugin_definition, OrderedPluginDefinition)
                sorter.add(plugin_definition.id)
                other_plugin_ids = plugin_ids - {plugin.plugin().id}
                for after in filter(plugin_definition.after, other_plugin_ids):
                    sorter.add(plugin_definition.id, after)
                for before in filter(plugin_definition.before, other_plugin_ids):
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
            return ServicePluginCollection(sorted_plugins)
        return ServicePluginCollection([plugins])

    async def _bootstrap_plugin(
        self, plugin_type_and_id: tuple[type[ServicePluginDefinition], MachineName]
    ) -> Plugin:
        plugin = await self._new_plugin(plugin_type_and_id)
        if isinstance(plugin, LifeCycle):
            await self.life_cycle.synchronize(plugin)
        return plugin

    async def _new_plugin(
        self, plugin_type_and_id: tuple[type[ServicePluginDefinition], MachineName]
    ) -> Plugin:
        plugin_type, plugin_id = plugin_type_and_id
        try:
            manufacturer = self._service_plugin_manufacturers[plugin_type][plugin_id]
        except KeyError:
            manufacturer = (await self._services.plugins[plugin_type][plugin_id]).cls
        return await self._services.factory.new(manufacturer)

    async def _expand_requires(
        self,
        sorter: TopologicalSorter[tuple[type[ServicePluginDefinition], MachineName]],
        origin_type: type[ServicePluginDefinition],
        origin_id: MachineName,
        include_origin: bool,
    ) -> None:
        origin = await self._services.plugins[origin_type][origin_id]
        origin_predecessors = set()
        for requirement in origin.requires:
            if isinstance(requirement, ServicePluginRequirement):
                requires_plugin = requirement.plugin.plugin()
                requires_plugin_type = type(requires_plugin)
                requires_plugin_id = requires_plugin.id
                origin_predecessors.add((requires_plugin_type, requires_plugin_id))
                await self._expand_requires(
                    sorter, requires_plugin_type, requires_plugin_id, True
                )
        if include_origin:
            sorter.add((origin_type, origin_id), *origin_predecessors)

    def __getitem__[ServicePluginDefinitionT: ServicePluginDefinition, PluginT: Plugin](
        self,
        plugin_type: type[
            Intersection[ServicePluginDefinitionT, PluginClsDefinition[PluginT]]
        ]
        | str,
        /,
    ) -> ServicePluginCollection[ServicePluginDefinitionT, PluginT]:
        if isinstance(plugin_type, str):
            plugin_type = self._services.plugins[plugin_type].type
        return self._service_plugins[plugin_type]

    def __iter__(self) -> Iterator[type[ServicePluginDefinition]]:
        return iter(self._service_plugins)


class ServicePluginProvider(ManagedLifeCycle, ServiceProvider):
    """
    A service plugin provider.
    """

    def __init__[ServicePluginTypesT: ServicePluginDefinition](
        self,
        *args: Any,
        service_plugin_services: ServiceLevel,
        service_plugin_types: ServicePluginTypes[ServicePluginTypesT] = (),
        service_plugins: ServicePlugins[ServicePluginTypesT] = (),
        support_plugins: SupportPlugins = (),
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__service_plugin_types = service_plugin_types
        self.__service_plugins = service_plugins
        self.__support_plugins = support_plugins
        self.__service_plugin_services = service_plugin_services

    @final
    @service
    async def service_plugins(self) -> ServicePluginManager:
        """
        The service plugins.
        """
        return ServicePluginManager(
            self.__service_plugin_services,
            self.__service_plugin_types,
            self.__service_plugins,
            self.__support_plugins,
        )
