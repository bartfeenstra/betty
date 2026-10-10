"""
Generic plugin API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.definition.id import resolve_id
from betty.localizables.gettext import _
from betty.localizables.markup import Quote, do_you_mean
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Iterable


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """


class PluginTypeNotFound(Invalid[MachineName], PluginError):
    """
    Raised when a plugin type cannot be found.
    """

    def __init__(
        self, plugin_type: MachineName, available_plugin_types: Iterable[MachineName], /
    ):
        super().__init__(
            plugin_type,
            _("Cannot find the {plugin_type} plugin type.").format(
                plugin_type=Quote(plugin_type)
            ),
            hint=do_you_mean(*[
                f'"{available_plugin_type}"'
                for available_plugin_type in available_plugin_types
            ]),
        )


class PluginNotFound(Invalid[MachineName], PluginError):
    """
    Raised when a plugin cannot be found.
    """

    def __init__[DefinitionT: PluginDefinition](
        self,
        plugin_type: type[DefinitionT],
        plugin: MachineName,
        available_plugins: Iterable[MachineName],
        /,
    ):
        super().__init__(
            plugin,
            _("Cannot find the {plugin_id} {plugin_type} plugin.").format(
                plugin_type=plugin_type.definition.label,
                plugin_id=Quote(plugin),
            ),
            hint=do_you_mean(*[
                f'"{resolve_id(available_plugin)}"'
                for available_plugin in available_plugins
            ]),
        )
