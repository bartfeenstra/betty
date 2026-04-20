"""
Multiple plugin instances services.
"""

from __future__ import annotations

from typing import final

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.service.plugin.instance import ServicePluginInstance
from betty.service.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)


@final
class PluginInstancesService[  # ty:ignore[abstract-method-in-final-class]
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    CollectionPluginInstanceServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, PluginT],
        PluginT,
    ],
    KeyedCollectionPluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
    ],
):  # ty:ignore[invalid-generic-class]
    """
    A service of plugins keyed by their IDs.
    """
