"""
Multiple plugin instances services.
"""

from __future__ import annotations

from typing import final

from betty.asyncio import ReAwaitable
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.services.plugin.instance import ServicePluginInstance
from betty.services.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)


@final
class PluginInstancesService[
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    CollectionPluginInstanceServiceManager[
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, PluginT],
        PluginT,
    ],
    KeyedCollectionPluginServiceManager[
        PluginDefinitionT,
        ReAwaitable[PluginT],
        ServicePluginInstance[PluginDefinitionT],
    ],
):
    """
    A service of plugins keyed by their IDs.
    """
