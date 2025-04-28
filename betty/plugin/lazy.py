"""
Lazily load plugins.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Generic, TypeVar

from typing_extensions import override

from betty.factory import Factory
from betty.json.schema import Schema
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginNotFound, PluginRepository

_PluginT = TypeVar("_PluginT", bound=Plugin)


class LazyPluginRepositoryBase(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Lazily load plugins.
    """

    def __init__(
        self, *, factory: Factory | None = None, schema_template: Schema | None = None
    ):
        super().__init__(factory=factory, schema_template=schema_template)
        self.__plugins: Mapping[str, type[_PluginT]] | None = None

    @override
    async def get(self, plugin_id: MachineName) -> type[_PluginT]:
        try:
            return (await self._plugins())[plugin_id]
        except KeyError:
            raise PluginNotFound.new(plugin_id, await self.select()) from None

    async def _plugins(self) -> Mapping[str, type[_PluginT]]:
        """
        Get the plugins, lazily loading them when needed.
        """
        if self.__plugins is None:
            self.__plugins = {
                plugin.plugin_id(): plugin for plugin in await self._load_plugins()
            }
        return self.__plugins

    @abstractmethod
    async def _load_plugins(self) -> Sequence[type[_PluginT]]:
        """
        Load the plugins.
        """

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        for plugin in (await self._plugins()).values():
            yield plugin
