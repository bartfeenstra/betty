"""
Tools to resolve wide varieties of generic plugin API types to specific types or plugin information.
"""

from __future__ import annotations

from typing import TypeAlias, overload

from typing_extensions import TypeVar

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.classed import ClassedPlugin, ClassedPluginDefinition

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_ClassedPluginT = TypeVar("_ClassedPluginT", bound=ClassedPlugin, default=ClassedPlugin)

ResolvableDefinition: TypeAlias = _PluginDefinitionT | type[_ClassedPluginT]
"""
Use :py:func:`betty.plugin.resolve.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""

ResolvableId: TypeAlias = (
    MachineName | ResolvableDefinition[_PluginDefinitionT, _ClassedPluginT]
)
"""
Use :py:func:`betty.plugin.resolve.resolve_id` to resolve this to a plugin ID.
"""


@overload
def resolve_definition(definition: _PluginDefinitionT, /) -> _PluginDefinitionT:
    pass


@overload
def resolve_definition(
    definition: type[_ClassedPluginT], /
) -> ClassedPluginDefinition[_ClassedPluginT]:
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
