"""
Provide plugin assertions.
"""

from collections.abc import Collection
from typing import Any, TypeVar

from betty.assertion import AssertionChain, assert_str
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


# @todo As this is right now, it's just an 'assert the value is one of theses statically defined values', which is not
# @todo at all specific to plugins.
# @todo
# @todo However, we do need the original version of this assertion (which returned PluginDefinition) for things like
# @todo assert_extension_has_assets_directory_path()
# @todo
# @todo
# @todo
def assert_plugin(
    plugins: Collection[MachineName], /
) -> AssertionChain[Any, MachineName]:
    """
    Assert that a value is a plugin ID.
    """

    def _assert(plugin_id: MachineName) -> MachineName:
        if plugin_id not in plugins:
            raise HumanFacingException(
                Paragraph(
                    _('Unknown plugin "{plugin}".').format(plugin_id=plugin_id),
                    do_you_mean(*(f'"{plugin}"' for plugin in plugins)),
                )
            )
        return plugin_id

    return assert_str() | _assert
