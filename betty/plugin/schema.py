"""
Access discovered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar

from betty.json.schema import Enum
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Iterable

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class PluginIdSchema(Enum, Generic[_PluginDefinitionT, _PluginT]):
    """
    The JSON schema for the IDs of the plugins in this repository.
    """

    def __init__(
        self,
        plugin_type: PluginTypeDefinition[_PluginT, _PluginDefinitionT],
        plugins: Iterable[PluginDefinition[_PluginT]],
        /,
    ):
        label = plugin_type.label.localize(DEFAULT_LOCALIZER)
        super().__init__(
            *[plugin.id for plugin in plugins],  # noqa A002
            def_name=kebab_case_to_lower_camel_case(plugin_type.id),
            title=label,
            description=f"A {label} plugin ID",
        )
