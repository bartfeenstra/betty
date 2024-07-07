"""
Integrates the plugin API with `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_.

Read more at :doc:`/usage/plugin/entry_point`.
"""

from importlib import metadata
from typing import Generic, TypeVar, final, Mapping

from betty.plugin import Plugin
from betty.plugin.lazy import LazyPluginRepositoryBase

_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class EntryPointPluginRepository(LazyPluginRepositoryBase[_PluginT], Generic[_PluginT]):
    """
    Discover plugins defined as `distribution package <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_ entry points.
    """

    def __init__(self, entry_point_group: str):
        super().__init__()
        self._entry_point_group = entry_point_group

    async def _load_plugins(self) -> Mapping[str, type[_PluginT]]:
        return {
            entry_point.name: entry_point.load()
            for entry_point in metadata.entry_points(
                group=self._entry_point_group,
            )
        }
