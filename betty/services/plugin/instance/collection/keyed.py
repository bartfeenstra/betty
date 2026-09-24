"""
Multiple plugin instances services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.asyncio import ReAwaitable
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition
from betty.plugin.factory import ManufacturablePlugin, PluginManufacturer
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.services.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)

if TYPE_CHECKING:
    from ty_extensions import Intersection


@final
class PluginInstancesService[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    PluginManufacturerT: PluginManufacturer,
    PluginT,
](
    CollectionPluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        KeyedPluginCollectionService[DefinitionT, ReAwaitable[PluginT]],
        PluginManufacturerT,
        PluginT,
    ],
    KeyedCollectionPluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        ReAwaitable[PluginT],
        ManufacturablePlugin[DefinitionT, PluginManufacturerT, PluginT],
    ],
):
    """
    A service of plugins keyed by their IDs.
    """
