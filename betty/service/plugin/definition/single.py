"""
Single plugin definition services.
"""

from __future__ import annotations

from typing import final, override

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.single import SinglePluginServiceManager


@final
class PluginDefinitionService[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
](
    SinglePluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ]
):
    """
    A single plugin definition service.
    """

    @override
    def new_service(self, service_provider: ServiceProviderT, /) -> PluginDefinitionT:
        return resolve_plugin_definition(self.get_plugins(service_provider)[0])
