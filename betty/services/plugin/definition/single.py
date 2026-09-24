"""
Single plugin definition services.
"""

from __future__ import annotations

from typing import final, override

from betty.definition import ResolvableDefinition, resolve_definition
from betty.plugin import PluginDefinition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.definition import PluginDefinitionServiceManager
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginDefinitionService[DefinitionT: PluginDefinition](
    PluginDefinitionServiceManager[
        ResolvableServiceLevelHasPluginServices, DefinitionT, DefinitionT
    ],
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        DefinitionT,
        ResolvableDefinition[DefinitionT],
    ],
):
    """
    A single plugin definition service.
    """

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> DefinitionT:
        return resolve_definition(self.get_plugins(owner)[0])
