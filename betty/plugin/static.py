"""
Provide static plugin management.
"""

from collections.abc import Iterator
from typing import Generic, TypeVar

from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, PluginNotFound, PluginRepository

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


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
    def get(self, plugin_id: MachineName) -> _PluginDefinitionT:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound.new(plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        yield from self._plugins.values()
