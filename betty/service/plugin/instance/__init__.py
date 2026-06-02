"""
Plugin instance services.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, final, override

from betty.asyncio import LazyReAwaitable, ReAwaitable
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.locale.localizable.gettext import _
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_id
from betty.service.plugin import PluginServiceManager, PluginServiceProvider
from betty.service.requirement import UnmetServiceRequirement

if TYPE_CHECKING:
    from betty.machine_name import MachineName

type ServicePluginInstance[PluginDefinitionT: PluginClsDefinition] = (
    PluginManufacturer[PluginDefinitionT, Plugin[PluginDefinitionT]]
    | ResolvablePluginDefinition[PluginDefinitionT]
)


type ServicePluginInstances[PluginDefinitionT: PluginClsDefinition] = Iterable[
    ServicePluginInstance[PluginDefinitionT]
]


class PluginInstanceServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginClsDefinition,
    GetServiceT,
    PluginT: Plugin,
](
    PluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        GetServiceT,
        ServicePluginInstance[PluginDefinitionT],
    ]
):
    """
    A service containing plugin instances.
    """

    @final
    def new_plugin_instance_service_item(
        self,
        service_provider: ServiceProviderT,
        item: ServicePluginInstance[PluginDefinitionT],
        /,
    ) -> ReAwaitable[PluginT]:
        """
        Create a new plugin instance service item from its init value.
        """

        async def _get_plugin() -> PluginT:
            plugin = await service_provider.services.factory.new(
                item.cls if isinstance(item, PluginClsDefinition) else item
            )
            if isinstance(plugin, Bootstrappable | Shutdownable):
                await service_provider.life_cycle.synchronize(plugin)
            return plugin

        return LazyReAwaitable(_get_plugin)

    @override
    async def prepare_plugins(
        self,
        service_provider: ServiceProviderT,
        /,
        *plugins: ServicePluginInstance[PluginDefinitionT],
    ) -> Iterable[ServicePluginInstance[PluginDefinitionT]]:
        # Deduplicate init plugins, ensuring there is at most one per plugin ID, where manufacturers override any other
        # init plugin definitions.
        deduplicated_plugins = {}
        for plugin in plugins:
            plugin_id = self.resolve_init_plugin_id(plugin)
            if plugin_id in deduplicated_plugins:
                if isinstance(deduplicated_plugins[plugin_id], PluginManufacturer):
                    if isinstance(plugin, PluginManufacturer):
                        raise UnmetServiceRequirement(
                            self,
                            _(
                                "Cannot add more than one manufacturer for the {plugin} {plugin_type} plugin to the {service} service."
                            ).format(
                                plugin=plugin_id,
                                plugin_type=self.plugin_type.type().label,
                                service=self.prop.id,
                            ),
                        )
                else:
                    deduplicated_plugins[plugin_id] = plugin
            else:
                deduplicated_plugins[plugin_id] = plugin
        return await super().prepare_plugins(
            service_provider, *deduplicated_plugins.values()
        )

    @override
    def resolve_init_plugin_id(
        self, plugin: ServicePluginInstance[PluginDefinitionT], /
    ) -> MachineName:
        if isinstance(plugin, PluginManufacturer):
            return plugin.plugin_id
        return resolve_plugin_id(plugin)
