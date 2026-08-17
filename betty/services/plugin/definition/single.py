"""
Single plugin definition services.
"""

from __future__ import annotations

from typing import final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin import PluginServiceManagerOwner
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginDefinitionService[
    OwnerT: PluginServiceManagerOwner,
    PluginDefinitionT: PluginDefinition,
](
    SinglePluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ]
):
    """
    A single plugin definition service.
    """

    @override
    def new_service(self, owner: OwnerT, /) -> PluginDefinitionT:
        return resolve_plugin_definition(self.get_plugins(owner)[0])
