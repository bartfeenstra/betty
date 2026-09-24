"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ReAwaitable
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.services.plugin.instance import PluginInstanceServiceManager

if TYPE_CHECKING:
    from ty_extensions import Intersection


class CollectionPluginInstanceServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    GetServiceT,
    PluginManufacturerT: PluginManufacturer,
    PluginT,
](
    PluginInstanceServiceManager[
        OwnerT,
        DefinitionT,
        GetServiceT,
        PluginManufacturerT,
        PluginT,
    ],
    CollectionPluginServiceManager[
        OwnerT,
        DefinitionT,
        GetServiceT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
    ],
):
    """
    A service of plugin instances.
    """

    @final
    @override
    def new_service_item(
        self,
        owner: OwnerT,
        plugin: ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
        /,
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, plugin)
