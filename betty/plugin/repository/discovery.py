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
    async def plugins(self) -> Collection[_PluginDefinitionT]:
        raise NotImplementedError

    @override
    def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        raise NotImplementedError


    async def _plugins(
        self
    ) -> PluginRepository[_PluginDefinitionT]:
        repository: PluginRepository[_PluginDefinitionT] | None
        if self._plugin_type.type().discoverer.overridden:
            return await self._new(plugin_type)
        # If the repository exists already, return it immediately so we avoid acquiring locks.
        repository = self._get(plugin_type)
        if repository:
            return repository
        async with self._ledger.ledger(f"{plugin_type.type().id}"):
            # The repository may have been created since we first checked.
            repository = self._get(plugin_type)
            if repository:
                return repository
            repository = await self._new(plugin_type)
            self._plugin_repositories[plugin_type] = repository
            return repository

    def _get(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginRepository[_PluginDefinitionT] | None:
        if plugin_type not in self._plugin_repositories:
            return None
        return self._plugin_repositories[plugin_type]

    async def _new(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginRepository[_PluginDefinitionT]:
        return StaticPluginRepository(
            plugin_type, *await plugin_type.type().discoverer.discover(self._services)
        )