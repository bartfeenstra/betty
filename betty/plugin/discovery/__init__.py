"""
Plugin discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from betty.service_level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@internal
class PluginDiscovery(Generic[_PluginDefinitionT], ABC):
    """
    A plugin discovery definition.
    """

    @abstractmethod
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        """
        Get the definitions for this plugin type.
        """


async def discover(
    service_level: ServiceLevel, *discoveries: PluginDiscovery[_PluginDefinitionT]
) -> Collection[_PluginDefinitionT]:
    """
    Discover plugins from multiple discoveries.
    """
    return [
        plugin
        for discovery in discoveries
        for plugin in await discovery.discover(service_level)
    ]
