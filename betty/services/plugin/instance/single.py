"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ReAwaitable
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition
from betty.plugin.cls.factory import NewPlugin
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.instance import PluginInstanceServiceManager
from betty.services.plugin.single import SinglePluginServiceManager

if TYPE_CHECKING:
    from ty_extensions import Intersection


@final
class PluginInstanceService[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    NewPluginT: NewPlugin,
    PluginT,
](
    PluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        ReAwaitable[PluginT],
        NewPluginT,
        PluginT,
    ],
    SinglePluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[DefinitionT, NewPluginT, PluginT],
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
