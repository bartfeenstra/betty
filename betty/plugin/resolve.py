"""
Tools to resolve wide varieties of generic plugin API types to specific types or plugin information.
"""

from __future__ import annotations

from typing import TypeAlias, overload

from typing_extensions import TypeVar

from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)

ResolvableDefinition: TypeAlias = _PluginDefinitionT | type[_PluginT]
"""
Use :py:func:`betty.plugin.resolve.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""

ResolvableId: TypeAlias = (
    MachineName | ResolvableDefinition[_PluginDefinitionT, _PluginT]
)
"""
Use :py:func:`betty.plugin.resolve.resolve_id` to resolve this to a plugin ID.
"""


@overload
def resolve_definition(definition: _PluginDefinitionT, /) -> _PluginDefinitionT:
    pass


@overload
def resolve_definition(definition: type[_PluginT], /) -> PluginDefinition[_PluginT]:
    pass


def resolve_definition(definition):
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition  # type: ignore[return-value]
    return definition.plugin


def resolve_id(plugin_id: ResolvableId, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, str):
        return plugin_id
    return resolve_definition(plugin_id).id
