"""
Access plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncIterator, Collection

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginRepository(ABC, Generic[_PluginDefinitionT]):
    """
    Access the plugins of a given type.
    """

    def __init__(self, plugin_type: builtins.type[_PluginDefinitionT], /):
        self._type = plugin_type

    @property
    def type(self) -> builtins.type[_PluginDefinitionT]:
        """
        The plugin type contained by this repository.
        """
        return self._type

    @abstractmethod
    async def ids(self) -> Collection[MachineName]:
        """
        Get the IDs of all plugins.
        """

    @abstractmethod
    async def plugin(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginUnavailable: if no plugin can be found for the given ID.
        """

    async def plugins(self) -> Collection[_PluginDefinitionT]:
        """
        Get all plugins.
        """
        return tuple(plugin async for plugin in self)

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        pass
