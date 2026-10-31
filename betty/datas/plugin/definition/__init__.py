"""
Reusable data for plugin definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from betty.datas.definition.id import (
    IdentifiableDefinitionConfig,
    IdentifiableDefinitionConfigDefinition,
)
from betty.definition import resolve_definition
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import ResolvableDataSamples
    from betty.definition import ResolvableDefinition


@final
class PluginDefinitionConfigDefinition[
    DefinitionT: Intersection[PluginDefinition, HumanFacingDefinition]
](IdentifiableDefinitionConfigDefinition[DefinitionT]):
    """
    Define a plugin definition.
    """

    def __init__(
        self,
        plugin_type: ResolvableDefinition[PluginTypeDefinition[DefinitionT]],
        /,
        *,
        samples: ResolvableDataSamples[Self, PluginDefinitionConfig[DefinitionT]]
        | None = None,
    ):
        plugin_type = resolve_definition(plugin_type)
        super().__init__(
            label=_("{plugin_type} configuration").format(
                plugin_type=plugin_type.label
            ),
            samples=samples,
        )


class PluginDefinitionConfig[DefinitionT: PluginDefinition](
    IdentifiableDefinitionConfig[DefinitionT]
):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.
    """
