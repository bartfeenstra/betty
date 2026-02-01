"""
Tools to automatically provide repositories for plugin types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.typing import threadsafe

if TYPE_CHECKING:
    from betty.collections import KeyedCollection
    from betty.machine_name import MachineName
    from betty.resolve import ResolvableId

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
        self,
        plugin_type: PluginTypeDefinition[_PluginDefinitionT]
        | type[_PluginDefinitionT]
        | MachineName,
        /,
    ) -> KeyedCollection[
        MachineName, ResolvableId[_PluginDefinitionT], _PluginDefinitionT
    ]:
        """
        Get the available plugins for the given type.
        """

    @property
    @abstractmethod
    def types(self) -> KeyedCollection[MachineName, MachineName, PluginTypeDefinition]:
        """
        Get the available plugin types.
        """
