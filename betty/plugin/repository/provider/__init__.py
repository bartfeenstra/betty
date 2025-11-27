"""
Tools to automatically provide repositories for plugin types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.plugin import PluginDefinition
from betty.typing import threadsafe

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@threadsafe
class PluginRepositoryProvider(ABC):
    """
    Provide plugin repositories.
    """

    @abstractmethod
    async def plugins(
        self,
        plugin_type: type[_PluginDefinitionT] | MachineName,
        *,
        check_requirements: bool = True,
    ) -> PluginRepository[_PluginDefinitionT]:
        """
        Get the plugin repository for a plugin type.
        """
