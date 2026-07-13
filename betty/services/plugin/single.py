"""
Single-item plugin services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.localizables.gettext import _
from betty.localizables.markup import JoinAnd
from betty.plugin import PluginDefinition
from betty.requirements.service import UnmetServiceRequirement
from betty.services.plugin import PluginServiceManager, PluginServiceProvider

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.resolve import ResolvablePluginDefinition


class SinglePluginServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
    InitT,
](PluginServiceManager[ServiceProviderT, PluginDefinitionT, GetServiceT, InitT]):
    """
    A service containing a single plugin item.
    """

    def __init__(self, plugin_type: type[PluginDefinitionT], /):
        super().__init__(plugin_type, auto=False)

    @final
    @override
    async def prepare_plugins(
        self,
        service_provider: ServiceProviderT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> Iterable[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        plugins = tuple(await super().prepare_plugins(service_provider, *plugins))
        # Ensure there is exactly one unique init plugin.
        if len(plugins) != 1:
            raise UnmetServiceRequirement(
                self,
                _(
                    "The {service} service must have exactly one {plugin_type} plugin, but {actual} were given."
                ).format(
                    service=self.prop.id,
                    plugin_type=self.plugin_type.type().label,
                    actual=JoinAnd(*map(self.resolve_init_plugin_id, plugins))
                    if plugins
                    else "0",
                ),
            )
        return plugins
