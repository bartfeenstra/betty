"""
Plugin definition collection services.
"""

from __future__ import annotations

from typing import final, override

from betty.definition import ResolvableDefinition, resolve_definition
from betty.plugin import PluginDefinition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.services.plugin.definition import PluginDefinitionServiceManager


class CollectionPluginDefinitionServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: PluginDefinition,
    GetServiceT,
](
    PluginDefinitionServiceManager[OwnerT, DefinitionT, GetServiceT],
    CollectionPluginServiceManager[
        OwnerT,
        DefinitionT,
        GetServiceT,
        DefinitionT,
        ResolvableDefinition[DefinitionT],
    ],
):
    """
    A service of plugin definitions.
    """

    @final
    @override
    def new_service_item(
        self,
        owner: OwnerT,
        plugin: ResolvableDefinition[DefinitionT],
        /,
    ) -> DefinitionT:
        return resolve_definition(plugin)
