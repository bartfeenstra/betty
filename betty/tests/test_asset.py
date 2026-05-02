from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from betty.asset import (
    AssetDirectoryDefinition,
    AssetRepository,
    AssetRepositoryService,
    StaticAssetRepository,
    UnknownAsset,
)
from betty.service.plugin import PluginServiceProvider
from betty.service_level import ServiceLevel


class TestAssetDirectoryDefinition:
    def test_assets(self, tmp_path: Path) -> None:
        sut = AssetDirectoryDefinition("my-first-asset", assets=tmp_path)
        assert sut.assets is tmp_path


class TestUnknownAsset:
    def test_new(self) -> None:
        path = Path("my-first-path")
        directories = (Path("my-first-assets"), Path("my-second-assets"))
        sut = UnknownAsset(path, directories)
        assert str(path) in str(sut)
        for asset_directory in directories:
            assert str(asset_directory) in str(sut)


class TestStaticAssetRepository:
    @pytest.fixture
    def sut_data(self, tmp_path: Path) -> tuple[AssetRepository, Path, Path]:
        source_path_1 = tmp_path / "one"
        source_path_1.mkdir()
        (source_path_1 / "apples").touch()
        (source_path_1 / "one").mkdir()
        (source_path_1 / "one" / "oranges").touch()
        (source_path_1 / "basket").mkdir()
        (source_path_1 / "basket" / "tomatoes").touch()
        (source_path_1 / "basket" / "aubergines").touch()

        source_path_2 = tmp_path / "two"
        source_path_2.mkdir()
        (source_path_2 / "apples").touch()
        (source_path_2 / "two").mkdir()
        (source_path_2 / "two" / "oranges").touch()
        (source_path_2 / "basket").mkdir()
        (source_path_2 / "basket" / "tomatoes").touch()
        (source_path_2 / "basket" / "courgettes").touch()

        return (
            StaticAssetRepository(source_path_1, source_path_2),
            source_path_1,
            source_path_2,
        )

    async def test_directories(self) -> None:
        with TemporaryDirectory() as source_1, TemporaryDirectory() as source_2:
            sut = StaticAssetRepository(source_1, source_2)
            assert sut.directories == (Path(source_1), Path(source_2))

    async def test_get(self, sut_data: tuple[AssetRepository, Path, Path]) -> None:
        sut, source_path_1, source_path_2 = sut_data
        assert await sut.get(Path("apples")) == source_path_1 / "apples"
        assert (
            await sut.get(Path("one") / "oranges") == source_path_1 / "one" / "oranges"
        )
        assert (
            await sut.get(Path("two") / "oranges") == source_path_2 / "two" / "oranges"
        )

    async def test_get__with_unknown_asset(
        self, sut_data: tuple[AssetRepository, Path, Path]
    ) -> None:
        sut, _, _ = sut_data
        with pytest.raises(UnknownAsset):
            await sut.get(Path("my-first-unknown-asset"))

    async def test_walk(self, sut_data: tuple[AssetRepository, Path, Path]) -> None:
        sut, _source_path_1, _source_path_2 = sut_data
        assert {path async for path in sut.walk()} == {
            Path("apples"),
            Path("basket") / "tomatoes",
            Path("basket") / "aubergines",
            Path("one") / "oranges",
            Path("two") / "oranges",
            Path("basket") / "courgettes",
        }

    async def test_walk_with_filter(
        self, sut_data: tuple[AssetRepository, Path, Path]
    ) -> None:
        sut, _source_path_1, _source_path_2 = sut_data
        assert {path async for path in sut.walk(Path("one"))} == {
            Path("one") / "oranges"
        }
        assert {path async for path in sut.walk(Path("two"))} == {
            Path("two") / "oranges"
        }
        assert {path async for path in sut.walk(Path("basket"))} == {
            Path("basket") / "tomatoes",
            Path("basket") / "aubergines",
            Path("basket") / "courgettes",
        }


class TestAssetRepositoryService:
    async def test_new_service(self) -> None:
        _ASSET = AssetDirectoryDefinition("my-first-asset", assets=Path(__file__))

        class _ServiceProvider(PluginServiceProvider):
            def __init__(self):
                super().__init__(
                    services=ServiceLevel(plugins={AssetDirectoryDefinition: [_ASSET]})
                )
                type(self).asset_directories.add_init_plugins(self, _ASSET)

            asset_directories = AssetRepositoryService()

        async with _ServiceProvider() as service_provider:
            assert list(service_provider.asset_directories.directories) == [
                _ASSET.assets
            ]
