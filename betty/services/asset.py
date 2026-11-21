"""
Asset services.
"""

from __future__ import annotations

from typing import final

from betty.asset import AssetDirectoryDefinition, AssetRepository, StaticAssetRepository
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService
from betty.services.simple import service


class HasAssets(ServiceLevel, HasPluginServices):
    """
    Expose assets from a variety of directories.
    """

    asset_directories = PluginDefinitionsService(AssetDirectoryDefinition)
    """
    The available asset directories.
    """

    @final
    @service
    def assets(self) -> AssetRepository:
        """
        The asset repository.
        """
        return StaticAssetRepository(
            *(asset.assets for asset in self.asset_directories)
        )
