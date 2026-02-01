"""
Provide plugin repositories for service levels.
"""

from __future__ import annotations

from collections import defaultdict
from importlib import metadata
from typing import TYPE_CHECKING, cast, final

from typing_extensions import TypeVar, override

from betty.concurrent import AsynchronizedLock, Ledger
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.collections import (
    PluginDefinitions,
    PluginTypeDefinitions,
    new_plugin_definitions,
    new_plugin_type_definitions,
)
from betty.plugin.manager import PluginManager

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from betty.collections import KeyedCollection
    from betty.machine_name import MachineName
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
        self._types: PluginTypeDefinitions | None = None
        self._plugins: MutableMapping[
            type[PluginDefinition], PluginDefinitions | None
        ] = defaultdict(None)
        self._ledger = Ledger(AsynchronizedLock.new_threadsafe())

    @override
    @property
    def types(self) -> KeyedCollection[MachineName, MachineName, PluginTypeDefinition]:
        if self._types is None:
            self._types = new_plugin_type_definitions(
                *(
                    entry_point.load()
                    for entry_point in metadata.entry_points(group="betty.plugin")
                )
            )

        return self._types

    @override
    async def plugins(
        self,
        plugin_type: PluginTypeDefinition[_PluginDefinitionT]
        | type[_PluginDefinitionT]
        | MachineName,
        /,
    ) -> PluginDefinitions[_PluginDefinitionT]:
        if isinstance(plugin_type, str):
            plugin_type = cast(type[_PluginDefinitionT], self.types[plugin_type])
        plugins: PluginDefinitions[_PluginDefinitionT] | None
        if plugin_type.type().discoverer.overridden:
            return await self._new(plugin_type)
        # If the definitions exist already, return them immediately so we avoid acquiring locks.
        plugins = self._get(plugin_type)
        if plugins:
            return plugins
        async with self._ledger.ledger(f"{plugin_type.type().id}"):
            # The definitions may have been created since we first checked.
            plugins = self._get(plugin_type)
            if plugins:
                return plugins
            plugins = await self._new(plugin_type)
            self._plugins[plugin_type] = plugins
            return plugins

    def _get(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginDefinitions[_PluginDefinitionT] | None:
        if plugin_type not in self._plugins:
            return None
        return self._plugins[plugin_type]

    async def _new(
        self, plugin_type: type[_PluginDefinitionT]
    ) -> PluginDefinitions[_PluginDefinitionT]:
        return new_plugin_definitions(
            *await plugin_type.type().discoverer.discover(services=self._services)
        )
