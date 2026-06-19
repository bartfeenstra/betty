"""
Plugin definition collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin import PluginServiceProvider
from betty.services.plugin.collection import CollectionPluginServiceManager


class CollectionPluginDefinitionServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
](
    CollectionPluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        GetServiceT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ]
):
    """
    A service of plugin definitions.
    """

    @final
    @override
    def new_service_item(
        self,
        service_provider: ServiceProviderT,
        plugin: ResolvablePluginDefinition[PluginDefinitionT],
        /,
    ) -> PluginDefinitionT:
        return resolve_plugin_definition(plugin)
