"""
Provide plugin assertions.
"""

from typing import Any, TypeVar

from betty.assertion import AssertionChain, assert_str
from betty.assertion.error import AssertionFailed
from betty.asyncio import wait_to_thread
from betty.locale.localizable import _
from betty.plugin import Plugin, PluginRepository, PluginNotFound

_PluginT = TypeVar("_PluginT", bound=Plugin)


def assert_plugin(
    plugin_repository: PluginRepository[_PluginT],
) -> AssertionChain[Any, type[_PluginT]]:
    """
    Assert that a value is a plugin ID.
    """

    def _assert(
        value: Any,
    ) -> type[_PluginT]:
        plugin_id = assert_str()(value)
        try:
            return wait_to_thread(plugin_repository.get(plugin_id))
        except PluginNotFound:
            raise AssertionFailed(
                _(
                    'Cannot find and import "{plugin_id}". Did you mean one of: {available_plugin_ids}?',
                ).format(
                    plugin_id=plugin_id,
                    available_plugin_ids=", ".join(
                        f'"{plugin.plugin_id()}"'
                        for plugin in wait_to_thread(plugin_repository.select())
                    ),
                )
            ) from None

    return AssertionChain(_assert)
