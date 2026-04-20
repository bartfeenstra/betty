"""
Multiple-item plugin services.
"""

from __future__ import annotations

from abc import abstractmethod
from asyncio import gather
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, final, override

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service.plugin import PluginServiceManager, PluginServiceProvider

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.resolve import ResolvablePluginDefinition


class CollectionPluginServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
    GetServiceItemT,
    InitT,
](PluginServiceManager[ServiceProviderT, PluginDefinitionT, GetServiceT, InitT]):
    """
    A service containing a collection of plugin items.
    """

    @override
    async def prepare_plugins(
        self,
        service_provider: ServiceProviderT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> Iterable[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:  # ty:ignore[invalid-method-override]
        plugins_by_id = {
            self.resolve_init_plugin_id(plugin): plugin
            for plugin in await super().prepare_plugins(service_provider, *plugins)
        }
        return (
            plugins_by_id[plugin_id]
            for plugin_id in self.__sort_plugins(
                await gather(
                    *map(
                        service_provider.services.plugins[self.plugin_type].get,
                        plugins_by_id.keys(),
                    )
                ),
            )
        )

    @final
    def __sort_plugins(
        self, plugins: Iterable[PluginDefinitionT]
    ) -> Iterable[MachineName]:
        plugins = sorted(plugins, key=lambda plugin: plugin.id)
        if issubclass(self.plugin_type, OrderedPluginDefinition):
            plugin_ids = {plugin.id for plugin in plugins}
            sorter = TopologicalSorter[MachineName]()
            for plugin in plugins:
                assert isinstance(plugin, OrderedPluginDefinition)
                sorter.add(plugin.id)
                other_plugin_ids = plugin_ids - {plugin.id}
                for after in filter(plugin.after, other_plugin_ids):
                    sorter.add(plugin.id, after)
                for before in filter(plugin.before, other_plugin_ids):
                    sorter.add(before, plugin.id)
            return sorter.static_order()
        return (plugin.id for plugin in plugins)

    @abstractmethod
    def new_service_item(
        self,
        service_provider: ServiceProviderT,
        plugin: InitT | ResolvablePluginDefinition[PluginDefinitionT],
        /,
    ) -> GetServiceItemT:
        """
        Create the new service item value for the given service provider.
        """
