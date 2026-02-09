"""
Provide plugin repositories for service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, final

from typing_extensions import TypeVar, override

from betty import plugin
from betty.concurrent import AsynchronizedLock, Ledger
from betty.plugin import PluginDefinition
from betty.plugin.manager import PluginManager

if TYPE_CHECKING:
    from collections.abc import Mapping

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
        self._plugins: Mapping[type[PluginDefinition], PluginRepository] | None = None
        self._ledger = Ledger(AsynchronizedLock.new_threadsafe())

    @override
    @property
    def types(self) -> plugin.PluginTypeRepository:
        return self._types

    @override
    def plugins(
        self, plugin_type: type[_PluginDefinitionT] | MachineName, /
    ) -> PluginRepository[_PluginDefinitionT]:
        if isinstance(plugin_type, str):
            plugin_type = cast(type[_PluginDefinitionT], self.types[plugin_type])
        if self._plugins is None:
            self._plugins = {
                plugin_type: DiscoverablePluginRepository(plugin_type)
                for plugin_type in self.types
            }
        return self._plugins[plugin_type]
