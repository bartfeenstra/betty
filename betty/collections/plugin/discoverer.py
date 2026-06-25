"""
Plugin discoverer collections.
"""

from __future__ import annotations

from typing import final, override

from betty.collections.keyed.error import ErroringKeyedCollection
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscoverer


@final
class PluginDiscovererCollection(
    ErroringKeyedCollection[
        MachineName, type[PluginDefinition] | MachineName | str, PluginDiscoverer
    ]
):
    """
    A collection of plugin discoverers.
    """

    @override
    def __getitem__[PluginDefinitionT: PluginDefinition = PluginDefinition](
        self, key: type[PluginDefinitionT] | MachineName | str
    ) -> PluginDiscoverer[PluginDefinitionT]:
        return super().__getitem__(key)  # ty:ignore[invalid-return-type]
