"""
Plugin instance collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.resolve import (
    ResolvablePluginDefinition as ResolvablePluginDefinition,
)
from betty.service.plugin.service import PluginServiceProvider
from betty.service.plugin.service.collection import CollectionPluginServiceManager
from betty.service.plugin.service.instance import (
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
):  # ty:ignore[invalid-generic-class]
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
