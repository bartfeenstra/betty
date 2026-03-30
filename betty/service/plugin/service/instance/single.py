"""
Single plugin instance services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.service.plugin.service import PluginServiceProvider
from betty.service.plugin.service.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)
from betty.service.plugin.service.single import SinglePluginServiceManager


@final
class PluginInstanceService[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    PluginInstanceServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        PluginT,
    ],
    SinglePluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
    ],
):  # ty:ignore[invalid-generic-class]
    """
    A single plugin service.
    """

    @override
    def new_service(
        self, service_provider: ServiceProviderT, /
    ) -> ReAwaitable[PluginT]:
        return self.new_plugin_instance_service_item(
            service_provider, self.get_plugins(service_provider)[0]
        )
