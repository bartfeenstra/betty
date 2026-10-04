"""
Plugin validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, Quote, do_you_mean
from betty.plugin import PluginDefinition
from betty.validation import Invalid
from betty.validators.str import is_str

if TYPE_CHECKING:
    from collections.abc import Collection


def is_plugin[DefinitionT: PluginDefinition](
    available_plugins: Collection[DefinitionT],
) -> Pipeline[Any, DefinitionT]:
    """
    Validate that a value is a plugin ID.
    """

    def _is_plugin(
        value: Any,
    ) -> DefinitionT:
        plugin_id = is_str(value)
        for plugin in available_plugins:
            if plugin.id == plugin_id:
                return plugin
        raise Invalid(
            Paragraph(
                _("Unknown plugin {plugin}.").format(plugin_id=Quote(plugin_id)),
                do_you_mean(*(f'"{plugin.id}"' for plugin in available_plugins)),
            )
        ) from None

    return Pipeline(_is_plugin)
