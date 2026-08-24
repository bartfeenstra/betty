"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginInstanceService[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        OwnerT,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        PluginT,
    ],
    SinglePluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
    ],
):
    """
    A single plugin service.
    """

    @override
    def new_service(self, owner: OwnerT, /) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(owner, self.get_plugins(owner)[0])
