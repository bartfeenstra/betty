"""
Provide static plugin management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.plugin import PluginDefinition, ResolvableDefinition, resolve_definition
from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.machine_name import ResolvableMachineName


@final
class StaticPluginRepository[PluginDefinitionT: PluginDefinition](
    PluginRepository[PluginDefinitionT]
):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(
        self,
        plugin_type: type[PluginDefinitionT],  # noqa: A002
        *plugins: ResolvableDefinition[PluginDefinitionT],
    ):
        super().__init__(plugin_type)
        self._plugins = {
            plugin.id: plugin
            for plugin in (resolve_definition(plugin) for plugin in plugins)
        }

    @override
    def get(self, plugin_id: ResolvableMachineName, /) -> PluginDefinitionT:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound(self.type.type(), plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[PluginDefinitionT]:
        yield from self._plugins.values()
