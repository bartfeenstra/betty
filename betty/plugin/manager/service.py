"""
Provide plugin repositories for service levels.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast, final

from typing_extensions import TypeVar, override

from betty import plugin
from betty.concurrent import AsynchronizedLock, Ledger
from betty.plugin import PluginDefinition
from betty.plugin.manager import PluginManager
from betty.plugin.repository.static import StaticPluginRepository

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class ServiceLevelPluginManager(PluginManager):
    """
    Manage plugins for a service level.
    """

    def __init__(self, services: ServiceLevel, /):
        self._services = services
        self._types = plugin.PluginTypeRepository()
        self._plugin_repositories: MutableMapping[
            type[PluginDefinition], PluginRepository[Any] | None
        ] = defaultdict(None)
        self._ledger = Ledger(AsynchronizedLock.new_threadsafe())

    @override
    @property
    def types(self) -> plugin.PluginTypeRepository:
        return self._types

    @override
    async def plugins(
        self, plugin_type: type[_PluginDefinitionT] | MachineName, /
    ) -> PluginRepository[_PluginDefinitionT]:
        if isinstance(plugin_type, str):
            plugin_type = cast(type[_PluginDefinitionT], self.types[plugin_type])
        repository: PluginRepository[_PluginDefinitionT] | None
        if plugin_type.type().discoverer.overridden:
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
