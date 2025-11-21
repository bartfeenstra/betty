"""
Tools to resolve wide varieties of generic plugin API types to specific types or plugin information.
"""

from __future__ import annotations

from typing import TypeAlias

from typing_extensions import TypeVar

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.classed import ClassedPlugin

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_ClassedPluginT = TypeVar("_ClassedPluginT", bound=ClassedPlugin, default=ClassedPlugin)

ResolvablePluginDefinition: TypeAlias = _PluginDefinitionT | type[_ClassedPluginT]
"""
Use :py:func:`betty.plugin.resolve.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""

ResolvablePluginId: TypeAlias = (
    MachineName | ResolvablePluginDefinition[_PluginDefinitionT, _ClassedPluginT]
)
"""
Use :py:func:`betty.plugin.resolve.resolve_id` to resolve this to a plugin ID.
"""


def resolve_definition(definition: ResolvablePluginDefinition, /) -> PluginDefinition:
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition
    return definition.plugin


def resolve_id(plugin_id: ResolvablePluginId, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, str):
        return plugin_id
    return resolve_definition(plugin_id).id
