"""
Plugin discoverer collections.
"""

from __future__ import annotations

from typing import final, override

from betty.collection.catalog import Catalog
from betty.collections.catalog.error import ErroringCatalog
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscoverer


# @todo What do we use this for again?
@final
class PluginDiscovererCollection(
    ErroringCatalog[
        MachineName,
        type[PluginDefinition] | MachineName | str,
        PluginDiscoverer,
        Catalog[
            MachineName, type[PluginDefinition] | MachineName | str, PluginDiscoverer
        ],
    ]
):
    """
    A collection of plugin discoverers.
    """

    @override
    def __getitem__[DefinitionT: PluginDefinition = PluginDefinition](
        self, key: type[DefinitionT] | MachineName | str
    ) -> PluginDiscoverer[DefinitionT]:
        return super().__getitem__(key)  # ty:ignore[invalid-return-type]
