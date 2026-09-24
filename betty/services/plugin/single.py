"""
Single-item plugin services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.localizables.gettext import _
from betty.localizables.markup import JoinAnd
from betty.plugin import PluginDefinition
from betty.requirements.service import UnmetServiceRequirement
from betty.services.plugin import (
    PluginServiceManager,
    ResolvableServiceLevelHasPluginServices,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.definition import ResolvableDefinition


class SinglePluginServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: PluginDefinition,
    GetServiceT,
    InitT,
](PluginServiceManager[OwnerT, DefinitionT, GetServiceT, InitT]):
    """
    A service containing a single plugin item.
    """

    def __init__(self, plugin_type: type[DefinitionT], /):
        super().__init__(plugin_type, auto=False)

    @final
    @override
    async def prepare_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: InitT | ResolvableDefinition[DefinitionT],
    ) -> Iterable[InitT | ResolvableDefinition[DefinitionT]]:
        plugins = tuple(await super().prepare_plugins(owner, *plugins))
        # Ensure there is exactly one unique init plugin.
        if len(plugins) != 1:
            raise UnmetServiceRequirement(
                self,
                _(
                    "The {service} service must have exactly one {plugin_type} plugin, but {actual} were given."
                ).format(
                    service=self.ownership.fully_qualified_name,
                    plugin_type=self.plugin_type.definition.label,
                    actual=JoinAnd(*map(self.resolve_init_plugin_id, plugins))
                    if plugins
                    else "0",
                ),
            )
        return plugins
