"""
Asset directory services.
"""

from betty.asset import AssetDirectoryDefinition, StaticAssetRepository
from betty.classtools.init import Init
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService


class HasAssetDirectories(Init):
    """
    An object that has an asset directories service.
    """

    asset_directories = PluginDefinitionsService(
        AssetDirectoryDefinition,
        new_service=lambda service, owner: StaticAssetRepository(
            *(
                service.new_service_item(owner, asset).assets
                for asset in service.get_plugins(owner)
            )
        ),
    )
