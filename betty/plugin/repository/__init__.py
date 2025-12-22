"""
Access discovered plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginRepository(ABC, Generic[_PluginDefinitionT]):
    """
    Access discovered plugins.
    """

    def __init__(self, plugin_type: type[_PluginDefinitionT]):
        self._type = plugin_type

    @property
    def type(self) -> type[_PluginDefinitionT]:
        """
        The plugin type contained by this repository.
        """
        return self._type

    @abstractmethod
    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginUnavailable: if no plugin can be found for the given ID.
        """

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    @abstractmethod
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        pass

    def __getitem__(self, plugin_id: MachineName) -> _PluginDefinitionT:
        return self.get(plugin_id)
