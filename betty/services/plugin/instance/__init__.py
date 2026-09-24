"""
Plugin instance services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import LazyReAwaitable, ReAwaitable
from betty.definition.cls import ClsDefinition
from betty.definition.id import resolve_id
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import resolve_service_level
from betty.services.plugin import (
    PluginServiceManager,
    ResolvableServiceLevelHasPluginServices,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.machine_name import MachineName


class PluginInstanceServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    GetServiceT,
    PluginManufacturerT: PluginManufacturer,
    PluginT,
](
    PluginServiceManager[
        OwnerT,
        DefinitionT,
        GetServiceT,
        ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
    ]
):
    """
    A service containing plugin instances.
    """

    @final
    def new_plugin_instance_service_item(
        self,
        owner: OwnerT,
        item: ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
        /,
    ) -> ReAwaitable[PluginT]:
        """
        Create a new plugin instance service item from its init value.
        """
        services = resolve_service_level(
            owner,  # ty:ignore[invalid-argument-type]
        )

        async def _get_plugin() -> PluginT:
            plugin = await services.factory.new(
                item.cls if isinstance(item, ClsDefinition) else item  # ty: ignore[invalid-argument-type]
            )
            if isinstance(plugin, Bootstrappable | Shutdownable):
                await owner.life_cycle.bind(plugin)
            return plugin

        return LazyReAwaitable(_get_plugin)

    @override
    async def prepare_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
    ) -> Iterable[ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT]]:
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
                                plugin_type=self.plugin_type.definition.label,
                                service=self.ownership.fully_qualified_name,
                            ),
                        )
                else:
                    deduplicated_plugins[plugin_id] = plugin
            else:
                deduplicated_plugins[plugin_id] = plugin
        return await super().prepare_plugins(owner, *deduplicated_plugins.values())

    @final
    @override
    def resolve_init_plugin_id(
        self,
        plugin: ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
        /,
    ) -> MachineName:
        if isinstance(plugin, PluginManufacturer):
            return plugin.plugin_id
        return resolve_id(
            plugin,  # ty: ignore[invalid-argument-type]
        )
