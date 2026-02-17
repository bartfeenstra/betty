"""
Access discovered plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterator

    from betty.machine_name import ResolvableMachineName


class PluginRepository[PluginDefinitionT: PluginDefinition = PluginDefinition](ABC):
    """
    Access discovered plugins.
    """

    def __init__(self, plugin_type: builtins.type[PluginDefinitionT]):
        self._type = plugin_type

    @property
    def type(self) -> builtins.type[PluginDefinitionT]:
        """
        The plugin type contained by this repository.
        """
        return self._type

    @abstractmethod
    def get(self, plugin_id: ResolvableMachineName, /) -> PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginUnavailable: if no plugin can be found for the given ID.
        """

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    @abstractmethod
    def __iter__(self) -> Iterator[PluginDefinitionT]:
        pass

    def __getitem__(self, plugin_id: ResolvableMachineName) -> PluginDefinitionT:
        return self.get(plugin_id)
