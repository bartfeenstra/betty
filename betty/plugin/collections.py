"""
Plugin collections.
"""

from typing import TypeAlias

from typing_extensions import TypeVar

from betty.collections import DictKeyedCollection, KeyedCollection
from betty.machine_name import MachineName
from betty.plugin import (
    PluginDefinition,
    PluginTypeDefinition,
    ResolvableDefinition,
    ResolvableId,
    resolve_definition,
    resolve_id,
)

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)

PluginDefinitions: TypeAlias = KeyedCollection[
    MachineName, ResolvableId[_PluginDefinitionT], _PluginDefinitionT
]
PluginTypeDefinitions: TypeAlias = KeyedCollection[
    MachineName, MachineName, PluginTypeDefinition
]


def new_plugin_definitions(
    *plugins: ResolvableDefinition[_PluginDefinitionT],
) -> PluginDefinitions[_PluginDefinitionT]:
    """
    Create a new collection of plugin definitions.
    """
    return DictKeyedCollection(
        {resolve_id(plugin.id): plugin for plugin in map(resolve_definition, plugins)},
        key_resolver=resolve_id,
    )


def new_plugin_type_definitions(
    *plugin_types: PluginTypeDefinition,
) -> PluginTypeDefinitions:
    """
    Create a new collection of plugin type definitions.
    """
    return DictKeyedCollection(
        {plugin_type.id: plugin_type for plugin_type in plugin_types}
    )
