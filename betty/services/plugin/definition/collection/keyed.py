"""
Keyed plugin definitions services.
"""

from __future__ import annotations

from typing import final

from betty.definition import ResolvableDefinition
from betty.plugin import PluginDefinition
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
    KeyedPluginCollectionService,
)
from betty.services.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)


@final
class PluginDefinitionsService[DefinitionT: PluginDefinition](
    CollectionPluginDefinitionServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        KeyedPluginCollectionService[DefinitionT, DefinitionT],
    ],
    KeyedCollectionPluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DefinitionT,
        DefinitionT,
        ResolvableDefinition[DefinitionT],
    ],
):
    """
    A service of plugin definitions keyed by their IDs.
    """
