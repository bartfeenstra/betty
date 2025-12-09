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
from betty.plugin.discovery import discover
from betty.plugin.repository.provider import PluginRepositoryProvider
from betty.plugin.repository.static import StaticPluginRepository
from betty.plugin.requirement import CheckRequirementRepository
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository
    from betty.service.level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@internal
@final
class ServiceLevelPluginRepositoryProvider(PluginRepositoryProvider):
    """
    Provide plugin repositories for service levels.
    """

    def __init__(self, services: ServiceLevel, /):
        self._services = services
        self._plugin_repositories: MutableMapping[
            type[PluginDefinition], MutableMapping[bool, PluginRepository[Any] | None]
        ] = defaultdict(
            lambda: {
                True: None,
                False: None,
            }
        )
        self._ledger = Ledger(AsynchronizedLock.new_threadsafe())

    @override
    async def plugins(
        self,
        plugin_type: type[_PluginDefinitionT] | MachineName,
        *,
        check_requirements: bool = True,
    ) -> PluginRepository[_PluginDefinitionT]:
        """
        Get the plugin repository for a plugin type.
        """
        if isinstance(plugin_type, str):
            plugin_type = cast(
                type[_PluginDefinitionT],
                plugin.plugin_types()[plugin_type],
            )
        repository: PluginRepository[_PluginDefinitionT] | None
        if plugin_type.type().discovery_overridden:
            repository = await self._new(plugin_type)
            if check_requirements:
                repository = await CheckRequirementRepository.new(
                    plugin_type, repository, self._services
                )
            return repository
        # If the repository exists already, return it immediately so we avoid acquiring locks.
        repository = self._get(plugin_type, check_requirements)
        if repository:
            return repository
        async with self._ledger.ledger(f"{plugin_type.type().id}:{check_requirements}"):
            # The repository may have been created since we first checked.
            repository = self._get(plugin_type, check_requirements)
            if repository:
                return repository
            if check_requirements:
                repository = await CheckRequirementRepository.new(
                    plugin_type,
                    await self.plugins(plugin_type, check_requirements=False),
                    self._services,
                )
            else:
                repository = await self._new(plugin_type)
            self._plugin_repositories[plugin_type][check_requirements] = repository
            return repository

    def _get(
        self, plugin_type: type[_PluginDefinitionT], check_requirements: bool = True
    ) -> PluginRepository[_PluginDefinitionT] | None:
        if plugin_type not in self._plugin_repositories:
            return None
        return self._plugin_repositories[plugin_type][check_requirements]

    async def _new(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginRepository[_PluginDefinitionT]:
        return StaticPluginRepository(
            plugin_type,
            *await discover(self._services, *plugin_type.type().discovery),
        )


_global_plugins = ServiceLevelPluginRepositoryProvider(None)
plugins = _global_plugins.plugins
"""
Get the plugin repository for a plugin type, for the global service level.
"""
