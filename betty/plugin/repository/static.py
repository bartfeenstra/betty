"""
Provide static plugin management.
"""

from collections.abc import Iterator
from typing import final

from typing_extensions import TypeVar, override

from betty.plugin import Plugin, PluginDefinition
from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository
from betty.plugin.resolve import ResolvableId, resolve_id

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class StaticPluginRepository(PluginRepository[_PluginDefinitionT, _PluginT]):
    """
    A repository that is given a static collection of plugins, and exposes those.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],  # noqa A002
        *plugins: _PluginDefinitionT,
    ):
        super().__init__(plugin_type)
        self._plugins = {plugin.id: plugin for plugin in plugins}

    @override
    def get(
        self, plugin_id: ResolvableId[_PluginDefinitionT, _PluginT], /
    ) -> _PluginDefinitionT:
        plugin_id = resolve_id(plugin_id)
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound(self.type.type, plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        yield from self._plugins.values()
