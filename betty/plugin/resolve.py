"""
Tools to resolve wide varieties of generic plugin API types to specific types or plugin information.
"""

from __future__ import annotations

from typing import TypeAlias

from typing_extensions import TypeVar

from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)

ResolvableDefinition: TypeAlias = _PluginDefinitionT | type[Plugin[_PluginDefinitionT]]
"""
Use :py:func:`betty.plugin.resolve.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""

ResolvableId: TypeAlias = MachineName | ResolvableDefinition[_PluginDefinitionT]
"""
Use :py:func:`betty.plugin.resolve.resolve_id` to resolve this to a plugin ID.
"""


def resolve_definition(
    definition: ResolvableDefinition[_PluginDefinitionT], /
) -> _PluginDefinitionT:
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition  # type: ignore[return-value]
    return definition.plugin()


def resolve_id(plugin_id: ResolvableId, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, str):
        return plugin_id
    return resolve_definition(plugin_id).id
