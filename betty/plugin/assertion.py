"""
Provide plugin assertions.
"""

from typing import Any, TypeVar

from betty.assertion import AssertionChain, assert_str
from betty.assertion.error import AssertionFailed
from betty.locale.localizable import _, join, do_you_mean
from betty.plugin import Plugin, PluginNotFound, PluginIdToTypeMap

_PluginT = TypeVar("_PluginT", bound=Plugin)


def assert_plugin(
    plugin_id_to_type_map: PluginIdToTypeMap[_PluginT],
) -> AssertionChain[Any, type[_PluginT]]:
    """
    Assert that a value is a plugin ID.
    """

    def _assert(
        value: Any,
    ) -> type[_PluginT]:
        plugin_id = assert_str()(value)
        try:
            return plugin_id_to_type_map[plugin_id]
        except PluginNotFound:
            raise AssertionFailed(
                join(
                    _(
                        'Cannot find and import "{plugin_id}".',
                    ).format(plugin_id=plugin_id),
                    do_you_mean(
                        *(f'"{plugin_id}"' for plugin_id in iter(plugin_id_to_type_map))
                    ),
                )
            ) from None

    return AssertionChain(_assert)
