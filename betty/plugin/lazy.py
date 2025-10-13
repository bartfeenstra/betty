"""
Lazily load plugins.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Generic, TypeVar

from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, PluginNotFound, PluginRepository

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


class LazyPluginRepositoryBase(
    PluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Lazily load plugins.
    """

    def __init__(
        self,
        plugin: type[_PluginDefinitionT],  # noqa A002
    ):
        super().__init__(plugin)
        self.__plugins: Mapping[str, _PluginDefinitionT] | None = None

    @override
    async def get(self, plugin_id: MachineName) -> _PluginDefinitionT:
        try:
            return (await self._plugins())[plugin_id]
        except KeyError:
            raise PluginNotFound.new(
                plugin_id, [plugin async for plugin in self]
            ) from None

    async def _plugins(self) -> Mapping[str, _PluginDefinitionT]:
        """
        Get the plugins, lazily loading them when needed.
        """
        if self.__plugins is None:
            self.__plugins = {
                plugin.id: plugin for plugin in await self._load_plugins()
            }
        return self.__plugins

    @abstractmethod
    async def _load_plugins(self) -> Sequence[_PluginDefinitionT]:
        """
        Load the plugins.
        """

    @override
    async def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        for plugin in (await self._plugins()).values():
            yield plugin
