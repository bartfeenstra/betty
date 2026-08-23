"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.instance import PluginInstanceServiceManager
from betty.services.plugin.single import SinglePluginServiceManager


@final
class PluginInstanceService[
    PluginDefinitionT: PluginClsDefinition,
    PluginManufacturerT: PluginManufacturer,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        PluginManufacturerT,
        PluginT,
    ],
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[PluginDefinitionT, PluginManufacturerT, PluginT],
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
