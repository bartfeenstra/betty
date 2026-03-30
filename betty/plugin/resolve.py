"""
Tools to resolve plugin-related typed.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Never, overload

from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition

if TYPE_CHECKING:
    from ty_extensions import Intersection

type ResolvablePluginTypeDefinition = (
    PluginTypeDefinition | type[PluginDefinition] | ResolvablePluginDefinition
)


type ResolvablePluginTypeId = ResolvablePluginTypeDefinition | ResolvableMachineName
"""
Use :py:func:`betty.plugin.resolve_plugin_type_id` to resolve this to a plugin type ID.
"""


@overload
def resolve_plugin_type_id(plugin_type_id: ResolvablePluginTypeId, /) -> MachineName:
    pass


@overload
def resolve_plugin_type_id(plugin_type_id: Any, /) -> MachineName | Never:
    pass


def resolve_plugin_type_id(plugin_type_id):
    """
    Resolve a plugin type identifier to a plugin type ID.

    :raises ValueError: Raised if the value cannot be resolved to a plugin type ID.
    """
    if isinstance(plugin_type_id, PluginTypeDefinition):
        return plugin_type_id.id
    if isinstance(plugin_type_id, str):
        return MachineName.resolve(plugin_type_id)
    if isinstance(plugin_type_id, type) and issubclass(
        plugin_type_id, PluginDefinition
    ):
        return plugin_type_id.type().id
    with suppress(ValueError):
        return resolve_plugin_definition(plugin_type_id).type().id
    raise ValueError(f"'{plugin_type_id}' cannot be resolved to a plugin type ID.")


type ResolvablePluginDefinition[
    PluginDefinitionT: PluginDefinition = PluginDefinition
] = (
    PluginDefinitionT
    | type[Plugin[Intersection[PluginDefinitionT, PluginClsDefinition]]]
)
"""
Use :py:func:`betty.plugin.resolve_plugin_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""


@overload
def resolve_plugin_definition[PluginDefinitionT: PluginDefinition](
    plugin_definition: ResolvablePluginDefinition[PluginDefinitionT], /
) -> PluginDefinitionT:
    pass


@overload
def resolve_plugin_definition[PluginDefinitionT: PluginDefinition](
    plugin_definition: ResolvablePluginDefinition[PluginDefinitionT] | Any, /
) -> PluginDefinitionT | Never:
    pass


def resolve_plugin_definition(plugin_definition):
    """
    Resolve a plugin definition.

    :raises ValueError: Raised if the value cannot be resolved to a plugin definition.
    """
    if isinstance(plugin_definition, PluginDefinition):
        return plugin_definition
    if isinstance(plugin_definition, type) and issubclass(plugin_definition, Plugin):
        return plugin_definition.plugin()
    raise ValueError(
        f"'{plugin_definition}' cannot be resolved to a plugin definition."
    )


type ResolvablePluginId[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    ResolvableMachineName | ResolvablePluginDefinition[PluginDefinitionT]
)
"""
Use :py:func:`betty.plugin.resolve_plugin_id` to resolve this to a plugin ID.
"""


@overload
def resolve_plugin_id(plugin_id: ResolvablePluginId, /) -> MachineName:
    pass


@overload
def resolve_plugin_id(plugin_id: Any, /) -> MachineName | Never:
    pass


def resolve_plugin_id(plugin_id):
    """
    Resolve a plugin identifier to a plugin ID.

    :raises ValueError: Raised if the value cannot be resolved to a plugin ID.
    """
    if isinstance(plugin_id, MachineName):
        return plugin_id
    if isinstance(plugin_id, str):
        return MachineName.resolve(plugin_id)
    with suppress(ValueError):
        return resolve_plugin_definition(plugin_id).id
    raise ValueError(f"'{plugin_id}' cannot be resolved to a plugin ID.") from None
