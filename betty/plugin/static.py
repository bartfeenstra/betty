"""
Provide static plugin management.
"""

from collections.abc import AsyncIterator
from typing import Generic, TypeVar, final

from typing_extensions import override

from betty.plugin import PluginRepository, Plugin, PluginNotFound
from betty.machine_id import MachineId

_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class StaticPluginRepository(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(self, *plugins: type[_PluginT]):
        self._plugins = {plugin.plugin_id(): plugin for plugin in plugins}

    @override
    async def get(self, plugin_id: MachineId) -> type[_PluginT]:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound.new(plugin_id) from None

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        for plugin in self._plugins.values():
            yield plugin
