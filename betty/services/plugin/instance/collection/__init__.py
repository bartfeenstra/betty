"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.services.plugin.instance import PluginInstanceServiceManager


class CollectionPluginInstanceServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    PluginDefinitionT: PluginClsDefinition,
    GetServiceT,
    PluginManufacturerT: PluginManufacturer,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        OwnerT,
        PluginDefinitionT,
        GetServiceT,
        PluginManufacturerT,
        PluginT,
    ],
    CollectionPluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        GetServiceT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[PluginDefinitionT, PluginManufacturerT, PluginT],
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
        plugin: ManufacturablePlugin[PluginDefinitionT, PluginManufacturerT, PluginT],
        /,
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, plugin)
