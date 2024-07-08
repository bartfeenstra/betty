"""
Integrates the plugin API with `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_.

Read more at :doc:`/usage/plugin/entry_point`.
"""

from collections.abc import AsyncIterator
from importlib import metadata
from typing import Generic, TypeVar, final

from typing_extensions import override
from betty.plugin import PluginRepository, Plugin, PluginNotFound, PluginId

_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class EntryPointPluginRepository(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Discover plugins defined as `distribution package <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_ entry points.
    """

    def __init__(self, entry_point_group: str):
        self._entry_point_group = entry_point_group
        self.__plugins: dict[str, type[_PluginT]] | None = None

    @override
    async def get(self, plugin_id: PluginId) -> type[_PluginT]:
        try:
            return (await self._plugins())[plugin_id]
        except KeyError:
            raise PluginNotFound.new(plugin_id) from None

    async def _plugins(self) -> dict[str, type[_PluginT]]:
        if self.__plugins is None:
            self.__plugins = {
                entry_point.name: entry_point.load()
                for entry_point in metadata.entry_points(
                    group=self._entry_point_group,
                )
            }
        return self.__plugins

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        for plugin in (await self._plugins()).values():
            yield plugin
