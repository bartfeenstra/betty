"""
Provide static plugin management.
"""

from collections.abc import AsyncIterator
from typing import Generic, TypeVar, final

from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, PluginNotFound, PluginRepository

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class StaticPluginRepository(
    PluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(
        self,
        plugin: type[_PluginDefinitionT],  # noqa A002
        *plugins: _PluginDefinitionT,
    ):
        super().__init__(plugin)
        self._plugins = {plugin.id: plugin for plugin in plugins}

    @override
    async def get(self, plugin_id: MachineName) -> _PluginDefinitionT:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound.new(
                plugin_id, [plugin async for plugin in self]
            ) from None

    @override
    async def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        for plugin in self._plugins.values():
            yield plugin
