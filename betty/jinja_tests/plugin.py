"""
The plugin test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.plugin.cls import Plugin as PluginType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.machine_name import MachineName
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.service_level import ServiceLevel


class Plugin(JinjaTest):
    """
    Provides tests for a specific plugin type.
    """

    def __init__(self, plugin_type: type[PluginDefinition], /):
        self._plugin_type = plugin_type

    @classmethod
    def discover(
        cls, services: ServiceLevel, /
    ) -> Iterable[ResolvableDiscovery[JinjaTestDefinition]]:
        """
        Discover all plugins.
        """
        for plugin_type in services.plugins:
            yield cls._create(plugin_type.type)

    @classmethod
    def _create(cls, plugin_type: type[PluginDefinition]) -> type[JinjaTest]:
        plugin_id = f"{plugin_type.type().id}-plugin"

        @JinjaTestDefinition(plugin_id, auto=True)
        class _Plugin(Plugin):
            def __init__(self):
                super().__init__(plugin_type)

        _Plugin.__doc__ = f"""
            .. plugin:: jinja-test:{plugin_id}
            """
        return _Plugin

    def __call__(self, /, value: Any, plugin_id: MachineName | None = None) -> bool:
        """
        :param plugin_id: If given, additionally ensure the value is an instance of this type.
        """
        if not isinstance(value, PluginType):
            return False
        if not isinstance(value.plugin(), self._plugin_type):
            return False
        return not (plugin_id is not None and value.plugin().id != plugin_id)
