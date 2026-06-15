"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.collection import CollectionPluginServiceManager
from betty.service.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)


class CollectionPluginInstanceServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginClsDefinition,
    GetServiceT,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        GetServiceT,
        PluginT,
    ],
    CollectionPluginServiceManager[
        ServiceProviderT,
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
        service_provider: ServiceProviderT,
        plugin: ServicePluginInstance[PluginDefinitionT],
        /,
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(service_provider, plugin)
