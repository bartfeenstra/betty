"""
Single plugin definition services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.services.plugin.single import SinglePluginServiceManager

if TYPE_CHECKING:
    from betty.services.plugin import ResolvableServiceLevelHasPluginServices


@final
class PluginDefinitionService[
    PluginDefinitionT: PluginDefinition,
](
    SinglePluginServiceManager[
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
