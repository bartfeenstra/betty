"""
Plugin assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.str import assert_str
from betty.exception import HumanFacingException
from betty.functools import Pipeline
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from collections.abc import Collection


def assert_plugin[PluginDefinitionT: PluginDefinition](
    available_plugins: Collection[PluginDefinitionT],
) -> Pipeline[Any, PluginDefinitionT]:
    """
    Assert that a value is a plugin ID.
    """

    def _assert(
        value: Any,
    ) -> PluginDefinitionT:
        plugin_id = assert_str()(value)
        for plugin in available_plugins:
            if plugin.id == plugin_id:
                return plugin
        raise HumanFacingException(
            Paragraph(
                _('Unknown plugin "{plugin_id}".').format(plugin_id=plugin_id),
                do_you_mean(*(f'"{plugin.id}"' for plugin in available_plugins)),
            )
        ) from None

    return Pipeline(_assert)
