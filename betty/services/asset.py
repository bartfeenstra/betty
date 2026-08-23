"""
Asset services.
"""

from __future__ import annotations

from typing import final, override

from betty.asset import AssetDirectoryDefinition, AssetRepository, StaticAssetRepository
from betty.services.plugin import ResolvableServiceLevelHasPluginServices
from betty.services.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)


@final
class AssetRepositoryService(
    CollectionPluginDefinitionServiceManager[
        ResolvableServiceLevelHasPluginServices,
        AssetDirectoryDefinition,
        AssetRepository,
    ]
):
    """
    A service of plugin definitions keyed by their IDs.
    """

    def __init__(self):
        super().__init__(AssetDirectoryDefinition)

    @override
    def new_service(
        self, instance: ResolvableServiceLevelHasPluginServices, /
    ) -> AssetRepository:
        return StaticAssetRepository(
            *(
                self.new_service_item(instance, asset).assets
                for asset in self.get_plugins(instance)
            )
        )
