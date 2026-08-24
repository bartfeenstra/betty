"""
Multiple-item plugin services.
"""

from __future__ import annotations

from typing import final, override

from betty.collection.keyed import KeyedCollection
from betty.collections.keyed.adapter import KeyedCollectionAdapter
from betty.collections.keyed.error import ErroringKeyedCollection
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager

type KeyedPluginCollectionService[PluginDefinitionT: PluginDefinition, ItemT] = (
    KeyedCollection[MachineName, ResolvablePluginId[PluginDefinitionT], ItemT]
)


class _PluginNotFound(PluginNotFound, KeyError):
    pass


class KeyedCollectionPluginServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    PluginDefinitionT: PluginDefinition,
    GetServiceItemT,
    InitT,
](
    CollectionPluginServiceManager[
        OwnerT,
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
        self, owner: OwnerT, /
    ) -> KeyedPluginCollectionService[PluginDefinitionT, GetServiceItemT]:
        return ErroringKeyedCollection[
            MachineName, ResolvablePluginId[PluginDefinitionT], GetServiceItemT
        ](
            KeyedCollectionAdapter[
                MachineName, ResolvablePluginId[PluginDefinitionT], GetServiceItemT
            ](
                {
                    self.resolve_init_plugin_id(plugin): self.new_service_item(
                        owner, plugin
                    )
                    for plugin in self.get_plugins(owner)
                },
                key_resolver=resolve_plugin_id,
            ),
            lambda error, key: _PluginNotFound(
                self.plugin_type,
                resolve_plugin_id(key),
                map(self.resolve_init_plugin_id, self.get_plugins(owner)),
            ),
        )
