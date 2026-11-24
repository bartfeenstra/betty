"""
The plugin test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from betty.definition import HasDefinition
from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import MachineName


@final
@JinjaTestDefinition("plugin", auto=True)
class Plugin(JinjaTest):
    """
    Provides tests for a specific plugin type.

    .. plugin:: jinja-test:plugin
    """

    def __call__(
        self,
        /,
        value: Any,
        plugin_type: MachineName,
        plugin_id: MachineName | None = None,
    ) -> bool:
        """
        :param plugin_id: If given, additionally ensure the value is an instance of this type.
        """
        if not isinstance(value, HasDefinition):
            return False
        if not isinstance(value.definition, PluginDefinition):
            return False
        if value.definition.definition.id != plugin_type:
            return False
        if plugin_id is None:
            return True
        return value.definition.id == plugin_id
