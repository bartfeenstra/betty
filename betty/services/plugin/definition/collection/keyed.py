"""
Keyed plugin definitions services.
"""

from __future__ import annotations

from typing import final

from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition
from betty.services.plugin import HasPluginServices
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.services.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)


@final
class PluginDefinitionsService[
    OwnerT: HasPluginServices,
    PluginDefinitionT: PluginDefinition,
](
    CollectionPluginDefinitionServiceManager[
        OwnerT,
        PluginDefinitionT,
        KeyedPluginCollectionService[PluginDefinitionT, PluginDefinitionT],
    ],
    KeyedCollectionPluginServiceManager[
        OwnerT,
        PluginDefinitionT,
        PluginDefinitionT,
        ResolvablePluginDefinition[PluginDefinitionT],
    ],
):
    """
    A service of plugin definitions keyed by their IDs.
    """
