"""
Provide static plugin management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository
from betty.plugin.resolve import ResolvableDefinition, resolve_definition

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class StaticPluginRepository(PluginRepository[_PluginDefinitionT]):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],  # noqa A002
        *plugins: ResolvableDefinition[_PluginDefinitionT],
    ):
        super().__init__(plugin_type)
        self._plugins = {
            plugin.id: plugin
            for plugin in (resolve_definition(plugin) for plugin in plugins)
        }

    @override
    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound(self.type.type(), plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        yield from self._plugins.values()
