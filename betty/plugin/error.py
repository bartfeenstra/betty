"""
Generic plugin API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.machine_name import ResolvableMachineName


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """


class PluginTypeNotFound(PluginError, HumanFacingException):
    """
    Raised when a plugin type cannot be found.
    """

    def __init__(
        self,
        plugin_type_not_found: ResolvableMachineName,
        available_plugin_types: Iterable[ResolvableMachineName],
        /,
    ):
        super().__init__(
            Paragraph(
                _('Cannot find the "{plugin_type}" plugin type.').format(
                    plugin_type=plugin_type_not_found
                ),
                do_you_mean(*[
                    f'"{available_plugin_type}"'
                    for available_plugin_type in available_plugin_types
                ]),
            )
        )


class PluginNotFound(PluginError, HumanFacingException):
    """
    Raised when a plugin cannot be found.
    """

    def __init__[PluginDefinitionT: PluginDefinition](
        self,
        plugin_type: type[PluginDefinitionT],
        plugin_not_found: ResolvableMachineName,
        available_plugins: Iterable[ResolvablePluginId[PluginDefinitionT]],
        /,
    ):
        super().__init__(
            Paragraph(
                _('Cannot find the "{plugin_id}" {plugin_type} plugin.').format(
                    plugin_type=plugin_type.type().label, plugin_id=plugin_not_found
                ),
                do_you_mean(*[
                    f'"{resolve_plugin_id(available_plugin)}"'
                    for available_plugin in available_plugins
                ]),
            )
        )
