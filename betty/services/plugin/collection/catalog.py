"""
Multiple-item plugin services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.collection.catalog import Catalog
from betty.collections.catalog.dict import FrozenDictCatalog
from betty.definition.id import ResolvableId, resolve_id
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

type PluginServiceCatalog[DefinitionT: PluginDefinition, ItemT] = Catalog[
    MachineName, ResolvableId[DefinitionT], ItemT
]

type PluginServiceCatalogType[
    DefinitionT: PluginDefinition,
    ServiceT: PluginServiceCatalog,
    ServiceItemT,
] = Intersection[ServiceT, PluginServiceCatalog[DefinitionT, ServiceItemT]]


class _PluginNotFound(PluginNotFound, KeyError):
    pass


class CatalogPluginServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: PluginDefinition,
    GetServiceT: PluginServiceCatalog,
    GetServiceItemT,
    InitT,
](
    CollectionPluginServiceManager[
        OwnerT, DefinitionT, GetServiceT, GetServiceItemT, InitT
    ]
):
    """
    A service containing a catalog of plugin items.
    """

    def __init__(
        self,
        plugin_type: type[DefinitionT],
        /,
        *,
        auto: bool = True,
        new_service: Callable[
            [Self, OwnerT],
            PluginServiceCatalogType[DefinitionT, GetServiceT, GetServiceItemT],
        ] = lambda self_, owner: self_._new_service_default(owner),
    ):
        super().__init__(plugin_type, auto=auto)
        self.__new_service = new_service

    @final
    @override
    def new_service(self, owner: OwnerT, /) -> GetServiceT:
        return self.__new_service(self, owner)

    @final
    def _new_service_default(
        self, owner: OwnerT, /
    ) -> PluginServiceCatalog[DefinitionT, GetServiceItemT]:
        return FrozenDictCatalog[
            MachineName, ResolvableId[DefinitionT], GetServiceItemT
        ](
            {
                self.resolve_init_plugin_id(plugin): self.new_service_item(
                    owner, plugin
                )
                for plugin in self.get_plugins(owner)
            },
            key=resolve_id,
        )
