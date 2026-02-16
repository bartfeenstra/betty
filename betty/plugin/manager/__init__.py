"""
Tools to automatically provide repositories for plugin types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition, PluginTypeRepository
from betty.typing import threadsafe

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.plugin.repository import PluginRepository

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@threadsafe
class PluginManager(ABC):
    """
    Find plugin types and plugins.
    """

    @abstractmethod
    async def plugins(
        self, plugin_type: type[_PluginDefinitionT] | ResolvableMachineName, /
    ) -> PluginRepository[_PluginDefinitionT]:
        """
        Get the available plugins for the given type.
        """

    @property
    @abstractmethod
    def types(self) -> PluginTypeRepository:
        """
        Get the available plugin types.
        """
