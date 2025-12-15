"""
Generic plugin API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from typing_extensions import TypeVar

from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.resolve import (
    ResolvableDefinition,
    ResolvableId,
    resolve_definition,
    resolve_id,
)
from betty.requirement import UnmetRequirement as GenericUnmetRequirement

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.machine_name import MachineName
    from betty.requirement import Requirement

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
        plugin_not_found: MachineName,
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


@final
class UnmetRequirement(PluginUnavailable, GenericUnmetRequirement):
    """
    Raised when a plugin has unmet requirements.
    """

    def __init__(self, plugin_type: ResolvableDefinition, requirement: Requirement, /):
        plugin_type = resolve_definition(plugin_type)
        super().__init__(
            requirement,
            summary=_('{plugin_type} "{plugin_id}" has unmet requirements').format(
                plugin_type=plugin_type.type().label, plugin_id=plugin_type.id
            ),
        )
