"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.services.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)

if TYPE_CHECKING:
    from betty.services.plugin import ResolvableServiceLevelHasPluginServices


class CollectionPluginInstanceServiceManager[
    PluginDefinitionT: PluginClsDefinition,
    GetServiceT,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        PluginDefinitionT,
        GetServiceT,
        PluginT,
    ],
    CollectionPluginServiceManager[
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
        owner: ResolvableServiceLevelHasPluginServices,
        plugin: ServicePluginInstance[PluginDefinitionT],
        /,
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, plugin)
