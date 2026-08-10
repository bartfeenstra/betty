"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.services.plugin import HasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.services.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)


class CollectionPluginInstanceServiceManager[
    OwnerT: HasPluginServices,
    PluginDefinitionT: PluginClsDefinition,
    GetServiceT,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        OwnerT,
        PluginDefinitionT,
        GetServiceT,
        PluginT,
    ],
    CollectionPluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        GetServiceT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
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
        plugin: ServicePluginInstance[PluginDefinitionT],
        /,
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, plugin)
