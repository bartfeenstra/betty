"""
Lazily load plugins.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping
from typing import Generic, TypeVar

from typing_extensions import override

from betty.factory import Factory
from betty.plugin import PluginRepository, Plugin, PluginNotFound
from betty.machine_name import MachineName

_PluginT = TypeVar("_PluginT", bound=Plugin)


class LazyPluginRepositoryBase(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Lazily load plugins.
    """

    def __init__(self, *, factory: Factory[_PluginT] | None = None):
        super().__init__(factory=factory)
        self.__plugins: Mapping[str, type[_PluginT]] | None = None

    @override
    async def get(self, plugin_id: MachineName) -> type[_PluginT]:
        try:
            return (await self._plugins())[plugin_id]
        except KeyError:
            raise await PluginNotFound.new(plugin_id, self) from None

    async def _plugins(self) -> Mapping[str, type[_PluginT]]:
        """
        Get the plugins, lazily loading them when needed.
        """
        if self.__plugins is None:
            self.__plugins = await self._load_plugins()
        return self.__plugins

    @abstractmethod
    async def _load_plugins(self) -> Mapping[str, type[_PluginT]]:
        """
        Load the plugins.
        """
        pass

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        for plugin in (await self._plugins()).values():
            yield plugin
