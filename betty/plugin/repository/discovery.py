"""
Access discovered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition
from betty.plugin.repository import PluginRepository

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class DiscoveryPluginRepository(PluginRepository[_PluginDefinitionT]):
    """
    Lazily discover plugins.
    """

    @override
    async def ids(self) -> Collection[MachineName]:
        raise NotImplementedError

    @override
    async def plugin(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        raise NotImplementedError

    @override
    def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        raise NotImplementedError
