"""
Tools to automatically provide repositories for plugin types.
"""

from __future__ import annotations

from collections import defaultdict
from importlib import metadata
from typing import TYPE_CHECKING, final, overload

from typing_extensions import TypeVar

from betty.concurrent import AsynchronizedLock, Ledger
from betty.plugin import PluginDefinition, resolve_type_definition
from betty.plugin.collections import (
    PluginDefinitions,
    PluginTypeDefinitions,
    new_plugin_definitions,
    new_plugin_type_definitions,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from ty_extensions import Intersection

    from betty.collections import KeyedCollection
    from betty.machine_name import MachineName
    from betty.plugin import Plugin, PluginTypeDefinition
    from betty.service.level import ServiceLevel

_PluginDefinitionCoT = TypeVar(
    "_PluginDefinitionCoT",
    bound=PluginDefinition,
    default=PluginDefinition,
    covariant=True,
)


@final
class PluginManager:
    """
    Manage plugins types and plugins.
    """

    def __init__(self, services: ServiceLevel, /):
        self._services = services
        self._types: PluginTypeDefinitions | None = None
        self._plugins: MutableMapping[
            type[PluginDefinition], PluginDefinitions | None
        ] = defaultdict(None)
        self._ledger = Ledger(AsynchronizedLock.new_threadsafe())

    @property
    def types(self) -> KeyedCollection[MachineName, MachineName, PluginTypeDefinition]:
        """
        The available plugin types.
        """
        if self._types is None:
            self._types = new_plugin_type_definitions(
                *(
                    entry_point.load()
                    for entry_point in metadata.entry_points(group="betty.plugin")
                )
            )

        return self._types

    @overload
    async def plugins(
        self,
        plugin_type: PluginTypeDefinition[
            Plugin[_PluginDefinitionCoT], _PluginDefinitionCoT
        ],
        /,
    ) -> PluginDefinitions[_PluginDefinitionCoT]:
        pass

    @overload
    async def plugins(
        self,
        plugin_type: type[
            Intersection[
                _PluginDefinitionCoT,
                PluginDefinition[Plugin[_PluginDefinitionCoT]],
            ]
        ],
        /,
    ) -> PluginDefinitions[_PluginDefinitionCoT]:
        pass

    async def plugins(self, plugin_type):
        """
        Get the available plugins for the given type.
        """
        resolved_plugin_type = resolve_type_definition(plugin_type)
        plugins: PluginDefinitions[_PluginDefinitionCoT] | None
        if resolved_plugin_type.discoverer.overridden:
            return await self._new(resolved_plugin_type)
        # If the definitions exist already, return them immediately so we avoid acquiring locks.
        plugins = self._get(resolved_plugin_type)
        if plugins:
            return plugins
        async with self._ledger.ledger(f"{resolved_plugin_type.id}"):
            # The definitions may have been created since we first checked.
            plugins = self._get(resolved_plugin_type)
            if plugins:
                return plugins
            plugins = await self._new(resolved_plugin_type)
            self._plugins[resolved_plugin_type.cls] = plugins
            return plugins

    def _get(
        self, plugin_type: PluginTypeDefinition[Plugin, _PluginDefinitionCoT]
    ) -> PluginDefinitions[_PluginDefinitionCoT] | None:
        if plugin_type.cls not in self._plugins:
            return None
        return self._plugins[plugin_type.cls]

    async def _new(
        self, plugin_type: PluginTypeDefinition[Plugin, _PluginDefinitionCoT]
    ) -> PluginDefinitions[_PluginDefinitionCoT]:
        return new_plugin_definitions(
            *await plugin_type.discoverer.discover(services=self._services)
        )
