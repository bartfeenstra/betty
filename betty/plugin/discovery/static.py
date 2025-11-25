"""
Statically define and discover plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition, Plugin
from betty.plugin.discovery import PluginDiscovery
from betty.plugin.resolve import ResolvableDefinition, resolve_definition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.service.level import ServiceLevel


_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class StaticDiscovery(
    PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT, _PluginT]
):
    """
    Statically define and discover plugins.
    """

    def __init__(self, *plugins: ResolvableDefinition[_PluginDefinitionT, _PluginT]):
        self._plugins = [resolve_definition(plugin) for plugin in plugins]
        reveal_type(plugins)
        reveal_type(self._plugins)
        reveal_type(resolve_definition)

    @override
    async def discover(self, services: ServiceLevel, /) -> Iterable[_PluginDefinitionT]:
        return self._plugins
