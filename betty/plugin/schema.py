"""
Access discovered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.json.schema import Enum
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Iterable


@final
class PluginIdSchema[PluginDefinitionT: PluginDefinition = PluginDefinition](Enum):
    """
    The JSON schema for the IDs of the plugins in this repository.
    """

    def __init__(
        self,
        plugin_type: PluginTypeDefinition[PluginDefinitionT],
        plugins: Iterable[PluginDefinitionT],
        /,
    ):
        label = plugin_type.label.localize(DEFAULT_LOCALIZER)
        super().__init__(
            *[plugin.id for plugin in plugins],
            def_name=kebab_case_to_lower_camel_case(plugin_type.id),
            title=label,
            description=f"A {label} plugin ID",
        )
