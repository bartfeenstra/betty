"""
Provide plugin repositories for service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, final

from typing_extensions import TypeVar, override

from betty import plugin
from betty.concurrent import AsynchronizedLock
from betty.plugin import PluginDefinition
from betty.plugin.discovery import discover
from betty.plugin.repository.provider import PluginRepositoryProvider
from betty.plugin.repository.static import StaticPluginRepository
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository
    from betty.service_level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@internal
@final
class ServiceLevelPluginRepositoryProvider(PluginRepositoryProvider):
    """
    Provide plugin repositories for service levels.
    """

    def __init__(self, service_level: ServiceLevel, /):
        self._service_level = service_level
        self._plugin_repositories: MutableMapping[
            PluginDefinition, PluginRepository
        ] = {}
        self._lock = AsynchronizedLock.new_threadsafe()

    @override
    async def plugins(
        self, plugin_type: type[_PluginDefinitionT] | MachineName, /
    ) -> PluginRepository[_PluginDefinitionT]:
        """
        Get the plugin repository for a plugin type.
        """
        if isinstance(plugin_type, str):
            plugin_type = cast(
                type[_PluginDefinitionT], plugin.plugin_types()[plugin_type]
            )
        if plugin_type.type.discovery_overridden:
            return await self._build(plugin_type)
        if plugin_type not in self._plugin_repositories:  # type: ignore[comparison-overlap]
            async with self._lock:
                if plugin_type not in self._plugin_repositories:  # type: ignore[comparison-overlap]
                    self._plugin_repositories[plugin_type] = await self._build(  # type: ignore[index]
                        plugin_type
                    )
        return self._plugin_repositories[plugin_type]  # type: ignore[index,return-value]

    async def _build(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginRepository[_PluginDefinitionT]:
        return StaticPluginRepository(
            plugin_type,
            *await discover(self._service_level, *plugin_type.type.discoveries),
        )


_global_plugins = ServiceLevelPluginRepositoryProvider(None)
plugins = _global_plugins.plugins
"""
Get the plugin repository for a plugin type, for the global service level.
"""
