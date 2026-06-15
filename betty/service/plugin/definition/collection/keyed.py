"""
Keyed plugin definitions services.
"""

from __future__ import annotations

from typing import final

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.service.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)


@final
class PluginDefinitionsService[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
](
    CollectionPluginDefinitionServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, PluginDefinitionT],
    ],
    KeyedCollectionPluginServiceManager[
        ServiceProviderT,
        PluginDefinitionT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ],
):
    """
    A service of plugin definitions keyed by their IDs.
    """
