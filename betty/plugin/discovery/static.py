"""
Statically define and discover plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.service_level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class StaticDiscovery(PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT]):
    """
    Statically define and discover plugins.
    """

    def __init__(self, *plugins: _PluginDefinitionT):
        self._plugins = plugins

    @override
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        return self._plugins
