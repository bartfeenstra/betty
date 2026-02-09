"""
Provide static plugin management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition, ResolvableDefinition, resolve_definition
from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class StaticPluginRepository(PluginRepository[_PluginDefinitionT]):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],  # noqa: A002
        *plugins: ResolvableDefinition[_PluginDefinitionT],
    ):
        super().__init__(plugin_type)
        self._plugins = {
            plugin.id: plugin
            for plugin in (resolve_definition(plugin) for plugin in plugins)
        }

    @override
    async def plugin(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        try:
            return self._plugins[plugin_id]  # ty:ignore[invalid-return-type]
        except KeyError:
            raise PluginNotFound(
                self.type.type(), plugin_id, await self.plugins()
            ) from None

    @override
    async def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        for value in self._plugins.values():
            yield value

    @override
    async def ids(self) -> Collection[MachineName]:
        return list(self._plugins)
