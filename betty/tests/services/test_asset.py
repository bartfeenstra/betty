from pathlib import Path

from betty.asset import AssetDirectoryDefinition
from betty.service_level import ServiceLevel
from betty.services.asset import AssetRepositoryService
from betty.services.plugin import HasPluginServices


class TestAssetRepositoryService:
    async def test_new_service(self) -> None:
        _ASSET = AssetDirectoryDefinition("my-first-asset", assets=Path(__file__))

        class _Owner(HasPluginServices):
            def __init__(self):
                super().__init__(
                    services=ServiceLevel(plugins={AssetDirectoryDefinition: [_ASSET]})
                )
                type(self).asset_directories.add_init_plugins(self, _ASSET)

            asset_directories = AssetRepositoryService()

        async with _Owner() as owner:
            assert list(owner.asset_directories.directories) == [_ASSET.assets]
