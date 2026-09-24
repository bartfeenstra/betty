"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ReAwaitable
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.instance import PluginInstanceServiceManager
from betty.services.plugin.single import SinglePluginServiceManager

if TYPE_CHECKING:
    from ty_extensions import Intersection


@final
class PluginInstanceService[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    PluginManufacturerT: PluginManufacturer,
    PluginT,
](
    PluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        ReAwaitable[PluginT],
        PluginManufacturerT,
        PluginT,
    ],
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
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
