"""
Plugin definition services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.definition import ResolvableDefinition
from betty.definition.id import resolve_id
from betty.plugin import PluginDefinition
from betty.services.plugin import (
    PluginServiceManager,
    ResolvableServiceLevelHasPluginServices,
)

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class PluginDefinitionServiceManager[
    OwnerT: ResolvableServiceLevelHasPluginServices,
    DefinitionT: PluginDefinition,
    GetServiceT,
](
    PluginServiceManager[
        OwnerT,
        DefinitionT,
        GetServiceT,
        ResolvableDefinition[DefinitionT],
    ]
):
    """
    A service containing plugin definitions.
    """

    @final
    @override
    def resolve_init_plugin_id(
        self,
        plugin: ResolvableDefinition[DefinitionT],
        /,
    ) -> MachineName:
        return resolve_id(plugin)
