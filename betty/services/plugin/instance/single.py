"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.services.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)
from betty.services.plugin.single import SinglePluginServiceManager

if TYPE_CHECKING:
    from betty.services.plugin import ResolvableServiceLevelHasPluginServices


@final
class PluginInstanceService[
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        PluginDefinitionT,
        ReAwaitable[PluginT],
        PluginT,
    ],
    SinglePluginServiceManager[
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
    ],
):
    """
    A single plugin service.
    """

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, self.get_plugins(owner)[0])
