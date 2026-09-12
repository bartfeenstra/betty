"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import (
    ClassedPluginDefinition,
    ManufacturablePlugin,
    NewPlugin,
    Plugin,
)
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.instance import PluginInstanceServiceManager
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginInstanceService[
    PluginDefinitionT: ClassedPluginDefinition,
    NewPluginT: NewPlugin,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        NewPluginT,
        PluginT,
    ],
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[PluginDefinitionT, NewPluginT, PluginT],
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
