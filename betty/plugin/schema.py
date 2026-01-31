"""
Access discovered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar

from betty.json.schema import Enum
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Iterable

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class PluginIdSchema(Enum):
    """
    The JSON schema for the IDs of the plugins in this repository.
    """

    def __init__(
        self,
        plugin_type: PluginTypeDefinition[_PluginDefinitionT],
        plugins: Iterable[_PluginDefinitionT],
        /,
    ):
        label = plugin_type.label.localize(DEFAULT_LOCALIZER)
        super().__init__(
            *[plugin.id for plugin in plugins],  # noqa: A002
            def_name=kebab_case_to_lower_camel_case(plugin_type.id),
            title=label,
            description=f"A {label} plugin ID",
        )
