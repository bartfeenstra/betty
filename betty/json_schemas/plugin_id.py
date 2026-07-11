"""
Access discovered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.localizer import default_localizer
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.portable import PortableMapping


def new_plugin_id_schema[PluginDefinitionT: PluginDefinition](
    plugin_type: PluginTypeDefinition[PluginDefinitionT],
    plugins: Iterable[PluginDefinitionT],
    /,
) -> PortableMapping:
    """
    Create a JSON schema for the IDs of the plugins of a type.
    """
    label = plugin_type.label.localize(default_localizer)
    def_name = kebab_case_to_lower_camel_case(plugin_type.id)
    return {
        "$ref": f"#/$defs/{def_name}",
        "$defs": {
            def_name: {
                "description": f"A {label} plugin ID",
                "options": [plugin.id for plugin in plugins],
                "title": label,
                "type": "enum",
            }
        },
    }
