"""
Test utilities for :py:mod:`betty.plugin.manager`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, cast, override

from betty.plugin import (
    Plugin,
    PluginDefinition,
    PluginTypeRepository,
    ResolvableDefinition,
    resolve_definition,
)
from betty.plugin.manager import PluginManager
from betty.plugin.repository.static import StaticPluginRepository
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping

    from betty.machine_name import ResolvableMachineName
    from betty.plugin.repository import PluginRepository


@threadsafe
class StaticPluginManager(PluginManager):
    """
    Manage static plugin definitions.
    """

    def __init__(
        self,
        plugins: Mapping[
            type[PluginDefinition],
            ResolvableDefinition | Iterable[ResolvableDefinition],
        ],
        /,
    ):
        self._plugins: Mapping[type[PluginDefinition], Collection[PluginDefinition]] = (
            defaultdict(
                tuple,
                {
                    plugin_type: [resolve_definition(plugin_type_plugins)]
                    if isinstance(plugin_type_plugins, PluginDefinition)
                    else [plugin_type_plugins]
                    if isinstance(plugin_type_plugins, type)
                    and issubclass(plugin_type_plugins, Plugin)
                    else plugin_type_plugins
                    for plugin_type, plugin_type_plugins in plugins.items()
                },
            )  # ty:ignore[invalid-assignment]
        )
        self._types = PluginTypeRepository()

    @override
    async def plugins[PluginDefinitionT: PluginDefinition](
        self, plugin_type: type[PluginDefinitionT] | ResolvableMachineName, /
    ) -> PluginRepository[PluginDefinitionT]:
        if isinstance(plugin_type, str):
            plugin_type = cast(type[PluginDefinitionT], self.types[plugin_type])
        return StaticPluginRepository(plugin_type, *self._plugins[plugin_type])  # ty:ignore[invalid-return-type]

    @override
    @property
    def types(self) -> PluginTypeRepository:
        return self._types
