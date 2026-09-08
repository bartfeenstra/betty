"""
Plugin definition collection services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin.collection import CollectionPluginServiceManager

if TYPE_CHECKING:
    from betty.service import ResolvableServiceLevelHasPluginServices


class CollectionPluginDefinitionServiceManager[
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
](
    CollectionPluginServiceManager[
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
        owner: ResolvableServiceLevelHasPluginServices,
        plugin: ResolvablePluginDefinition[PluginDefinitionT],
        /,
    ) -> PluginDefinitionT:
        return resolve_plugin_definition(plugin)
