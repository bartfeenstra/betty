"""
Statically define and discover plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery
from betty.plugin.resolve import ResolvableDefinition, resolve_definition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.service.level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class StaticDiscovery(PluginDiscovery[_PluginDefinitionT]):
    """
    Statically define and discover plugins.
    """

    def __init__(self, *plugins: ResolvableDefinition[_PluginDefinitionT]):
        self._plugins = tuple(resolve_definition(plugin) for plugin in plugins)

    @override
    async def discover(self, services: ServiceLevel, /) -> Iterable[_PluginDefinitionT]:
        return self._plugins
