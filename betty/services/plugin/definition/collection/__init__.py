"""
Plugin definition collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager


class CollectionPluginDefinitionServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
](
    CollectionPluginServiceManager[
        OwnerT,
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
        owner: OwnerT,
        plugin: ResolvablePluginDefinition[PluginDefinitionT],
        /,
    ) -> PluginDefinitionT:
        return resolve_plugin_definition(plugin)
