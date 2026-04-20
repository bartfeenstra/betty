"""
Multiple-item plugin services.
"""

from __future__ import annotations

from typing import final, override

from betty.collection.keyed import KeyedCollection
from betty.collection.keyed.adapter import KeyedCollectionAdapter
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.collection import CollectionPluginServiceManager

type KeyedPluginCollectionService[PluginDefinitionT: PluginDefinition, ItemT] = (
    KeyedCollection[MachineName, ResolvablePluginId[PluginDefinitionT], ItemT]
)


class KeyedCollectionPluginServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
    GetServiceItemT,
    InitT,
](
    CollectionPluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, GetServiceItemT],
        GetServiceItemT,
        InitT,
    ]
):
    """
    A service containing a keyed collection of plugin items.
    """

    @final
    @override
    def new_service(
        self, service_provider: ServiceProviderT, /
    ) -> KeyedPluginCollectionService[PluginDefinitionT, GetServiceItemT]:
        return KeyedCollectionAdapter(
            {
                self.resolve_init_plugin_id(plugin): self.new_service_item(
                    service_provider, plugin
                )
                for plugin in self.get_plugins(service_provider)
            },
            key_resolver=resolve_plugin_id,
        )
