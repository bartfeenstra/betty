"""
Single plugin definition services.
"""

from __future__ import annotations

from typing import final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginDefinitionService[PluginDefinitionT: PluginDefinition](
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ]
):
    """
    A single plugin definition service.
    """

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> PluginDefinitionT:
        return resolve_plugin_definition(self.get_plugins(owner)[0])
