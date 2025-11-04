"""
Provide plugin assertions.
"""

from typing import Any, TypeVar

from betty.assertion import AssertionChain, assert_str
from betty.exception import HumanFacingException
from betty.locale.localizable import Paragraph, _, do_you_mean
from betty.plugin import (
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
)

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


def assert_plugin(
    plugins: PluginRepository[_PluginDefinitionT],
) -> AssertionChain[Any, _PluginDefinitionT]:
    """
    Assert that a value is a plugin ID.
    """

    def _assert(
        value: Any,
    ) -> _PluginDefinitionT:
        plugin_id = assert_str()(value)
        try:
            return plugins[plugin_id]
        except PluginNotFound:
            raise HumanFacingException(
                Paragraph(
                    _(
                        'Cannot find and import "{plugin_id}".',
                    ).format(plugin_id=plugin_id),
                    do_you_mean(*(f'"{plugin.id}"' for plugin in plugins)),
                )
            ) from None

    return AssertionChain(_assert)
