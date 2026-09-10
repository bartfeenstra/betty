"""
Multiple plugin instances services.
"""

from __future__ import annotations

from typing import final

from betty.asyncio import ReAwaitable
from betty.plugin.cls import (
    ClassedPluginDefinition,
    ManufacturablePlugin,
    Plugin,
    PluginManufacturer,
)
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.services.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)


@final
class PluginInstancesService[
    PluginDefinitionT: ClassedPluginDefinition,
    PluginManufacturerT: PluginManufacturer,
    PluginT: Plugin,
](
    CollectionPluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, ReAwaitable[PluginT]],
        PluginManufacturerT,
        PluginT,
    ],
    KeyedCollectionPluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[PluginDefinitionT, PluginManufacturerT, PluginT],
    ],
):
    """
    A service of plugins keyed by their IDs.
    """
