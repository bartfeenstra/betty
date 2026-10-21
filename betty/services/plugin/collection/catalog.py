"""
Multiple-item plugin services.
"""

from __future__ import annotations

from typing import final, override

from betty.collection.catalog import Catalog
from betty.collections.catalog.dict import FrozenDictCatalog
from betty.collections.catalog.error import ErroringCatalog
from betty.definition.id import ResolvableId, resolve_id
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager

type KeyedPluginCollectionService[DefinitionT: PluginDefinition, ItemT] = Catalog[
    MachineName, ResolvableId[DefinitionT], ItemT
]


class _PluginNotFound(PluginNotFound, KeyError):
    pass


class CatalogPluginServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: PluginDefinition,
    GetServiceItemT,
    InitT,
](
    CollectionPluginServiceManager[
        OwnerT,
        DefinitionT,
        KeyedPluginCollectionService[DefinitionT, GetServiceItemT],
        GetServiceItemT,
        InitT,
    ]
):
    """
    A service containing a catalog of plugin items.
    """

    @final
    @override
    def new_service(
        self, owner: OwnerT, /
    ) -> KeyedPluginCollectionService[DefinitionT, GetServiceItemT]:
        return ErroringCatalog(
            FrozenDictCatalog[MachineName, ResolvableId[DefinitionT], GetServiceItemT](
                {
                    self.resolve_init_plugin_id(plugin): self.new_service_item(
                        owner, plugin
                    )
                    for plugin in self.get_plugins(owner)
                },
                key_resolver=resolve_id,
            ),
            lambda error, key: _PluginNotFound(
                self.plugin_type,
                resolve_id(key),
                map(self.resolve_init_plugin_id, self.get_plugins(owner)),
            ),
        )
