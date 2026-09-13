"""
Plugin instance services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import LazyReAwaitable, ReAwaitable
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.localizables.gettext import _
from betty.plugin.cls import (
    AnyPluginFactory,
    ClassedPluginDefinition,
    ManufacturablePlugin,
    NewPlugin,
    Plugin,
)
from betty.plugin.factory import new
from betty.plugin.resolve import resolve_plugin_id
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import resolve_service_level
from betty.services.plugin import (
    PluginServiceManager,
    ResolvableServiceLevelHasPluginServices,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.machine_name import MachineName


class PluginInstanceServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    PluginDefinitionT: ClassedPluginDefinition,
    GetServiceT,
    NewPluginT: NewPlugin,
    PluginT: Plugin,
](
    PluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        GetServiceT,
        ManufacturablePlugin[PluginDefinitionT, NewPluginT, PluginT],
    ]
):
    """
    A service containing plugin instances.
    """

    @final
    def new_plugin_instance_service_item(
        self,
        owner: OwnerT,
        item: ManufacturablePlugin[PluginDefinitionT, NewPluginT, PluginT],
        /,
    ) -> ReAwaitable[PluginT]:
        """
        Create a new plugin instance service item from its init value.
        """
        services = resolve_service_level(
            owner,  # ty:ignore[invalid-argument-type]
        )

        async def _get_plugin() -> PluginT:
            plugin = await new(
                item.cls if isinstance(item, ClassedPluginDefinition) else item,
                services,
            )
            if isinstance(plugin, Bootstrappable | Shutdownable):
                await owner.life_cycle.synchronize(plugin)
            return plugin

        return LazyReAwaitable(_get_plugin)

    @override
    async def prepare_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: ManufacturablePlugin[PluginDefinitionT, NewPluginT, PluginT],
    ) -> Iterable[ManufacturablePlugin[PluginDefinitionT, NewPluginT, PluginT]]:
        # Deduplicate init plugins, ensuring there is at most one per plugin ID, where manufacturers override any other
        # init plugin definitions.
        deduplicated_plugins = {}
        for plugin in plugins:
            plugin_id = self.resolve_init_plugin_id(plugin)
            if plugin_id in deduplicated_plugins:
                if isinstance(deduplicated_plugins[plugin_id], NewPlugin):
                    if isinstance(plugin, NewPlugin):
                        raise UnmetServiceRequirement(
                            self,
                            _(
                                "Cannot add more than one manufacturer for the {plugin} {plugin_type} plugin to the {service} service."
                            ).format(
                                plugin=plugin_id,
                                plugin_type=self.plugin_type.type().label,
                                service=self.ownership.fully_qualified_name,
                            ),
                        )
                else:
                    deduplicated_plugins[plugin_id] = plugin
            else:
                deduplicated_plugins[plugin_id] = plugin
        return await super().prepare_plugins(owner, *deduplicated_plugins.values())

    @override
    def resolve_init_plugin_id(
        self, plugin: AnyPluginFactory[PluginT, NewPluginT], /
    ) -> MachineName:
        if isinstance(plugin, NewPlugin):
            return plugin.id
        return resolve_plugin_id(plugin)
