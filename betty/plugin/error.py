"""
Generic plugin API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, final

from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin import (
    PluginDefinition,
    PluginTypeDefinition,
    ResolvableId,
    resolve_id,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.machine_name import ResolvableMachineName

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """


class PluginUnavailable(PluginError, HumanFacingException):
    """
    Raised when a plugin is unavailable for use.
    """


@final
class PluginNotFound(PluginUnavailable):
    """
    Raised when a plugin cannot be found.
    """

    def __init__(
        self,
        plugin_type: PluginTypeDefinition[Any, _PluginDefinitionT],
        plugin_not_found: ResolvableMachineName,
        available_plugins: Sequence[ResolvableId[_PluginDefinitionT]],
        /,
    ):
        super().__init__(
            Paragraph(
                _('Could not find a(n) {plugin_type} plugin "{plugin_id}".').format(
                    plugin_type=plugin_type.label, plugin_id=plugin_not_found
                ),
                do_you_mean(
                    *[
                        f'"{resolve_id(available_plugin)}"'
                        for available_plugin in available_plugins
                    ]
                ),
            )
        )
