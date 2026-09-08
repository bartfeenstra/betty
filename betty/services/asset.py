"""
Asset services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asset import AssetDirectoryDefinition, AssetRepository, StaticAssetRepository
from betty.services.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)

if TYPE_CHECKING:
    from betty.service import ResolvableServiceLevelHasServices


@final
class AssetRepositoryService(
    CollectionPluginDefinitionServiceManager[AssetDirectoryDefinition, AssetRepository]
):
    """
    A service of plugin definitions keyed by their IDs.
    """

    def __init__(self):
        super().__init__(AssetDirectoryDefinition)

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasServices, /
    ) -> AssetRepository:
        return StaticAssetRepository(
            *(
                self.new_service_item(owner, asset).assets
                for asset in self.get_plugins(owner)
            )
        )
