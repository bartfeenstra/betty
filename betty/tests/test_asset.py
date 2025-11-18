from pathlib import Path

import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.asset import (
    AssetRepository,
    ProxyAssetRepository,
    StaticAssetRepository,
    UnknownAsset,
)


class TestUnknownAsset:
    def test_new(self) -> None:
        path = Path("my-first-path")
        assets_directory_paths = (Path("my-first-assets"), Path("my-second-assets"))
        sut = UnknownAsset(path, assets_directory_paths)
        assert str(path) in str(sut)
        for assets_directory_path in assets_directory_paths:
            assert str(assets_directory_path) in str(sut)


class TestStaticAssetRepository:
    @pytest.fixture
    def sut(self, tmp_path: Path) -> tuple[AssetRepository, Path, Path]:
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

    async def test_assets_directory_paths(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                sut = StaticAssetRepository(source_path_1, source_path_2)
                assert sut.assets_directory_paths == (source_path_1, source_path_2)

    async def test_get(self, sut: tuple[AssetRepository, Path, Path]) -> None:
        sut, source_path_1, source_path_2 = sut
        assert await sut.get(Path("apples")) == source_path_1 / "apples"
        assert (
            await sut.get(Path("one") / "oranges") == source_path_1 / "one" / "oranges"
        )
        assert (
            await sut.get(Path("two") / "oranges") == source_path_2 / "two" / "oranges"
        )

    async def test_get__with_unknown_asset(
        self, sut: tuple[AssetRepository, Path, Path]
    ) -> None:
        sut, _, _ = sut
        with pytest.raises(UnknownAsset):
            await sut.get(Path("my-first-unknown-asset"))

    async def test_walk(self, sut: tuple[AssetRepository, Path, Path]) -> None:
        sut, source_path_1, source_path_2 = sut
        assert {path async for path in sut.walk()} == {
            Path("apples"),
            Path("basket") / "tomatoes",
            Path("basket") / "aubergines",
            Path("one") / "oranges",
            Path("two") / "oranges",
            Path("basket") / "courgettes",
        }

    async def test_walk_with_filter(
        self, sut: tuple[AssetRepository, Path, Path]
    ) -> None:
        sut, source_path_1, source_path_2 = sut
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


class TestProxyAssetRepository:
    def test_assets_directory_paths(self, tmp_path: Path) -> None:
        assets_directory_path_one = tmp_path / "one"
        assets_directory_path_two = tmp_path / "two"

        upstream_one = StaticAssetRepository(assets_directory_path_one)
        upstream_two = StaticAssetRepository(assets_directory_path_two)
        sut = ProxyAssetRepository(upstream_one, upstream_two)

        assert list(sut.assets_directory_paths) == [
            assets_directory_path_one,
            assets_directory_path_two,
        ]

    def test_assets_directory_paths__without_upstreams(self) -> None:
        sut = ProxyAssetRepository()
        assert not sut.assets_directory_paths

    async def test_walk(self, tmp_path: Path) -> None:
        assets_directory_path_one = tmp_path / "one"
        assets_directory_path_one.mkdir()
        assets_directory_path_two = tmp_path / "two"
        assets_directory_path_two.mkdir()

        asset_one_path = Path("one")
        (assets_directory_path_one / asset_one_path).touch()

        asset_two_path = Path("two")
        (assets_directory_path_two / asset_two_path).touch()

        common_asset_path = Path("common")
        (assets_directory_path_one / common_asset_path).touch()
        (assets_directory_path_two / common_asset_path).touch()

        upstream_one = StaticAssetRepository(assets_directory_path_one)
        upstream_two = StaticAssetRepository(assets_directory_path_two)
        sut = ProxyAssetRepository(upstream_one, upstream_two)

        assert {path async for path in sut.walk()} == {
            Path("one"),
            Path("two"),
            Path("common"),
        }

    async def test_walk__without_upstreams(self) -> None:
        sut = ProxyAssetRepository()
        assert not [path async for path in sut.walk()]

    async def test_get(self, tmp_path: Path) -> None:
        assets_directory_path_one = tmp_path / "one"
        assets_directory_path_one.mkdir()
        assets_directory_path_two = tmp_path / "two"
        assets_directory_path_two.mkdir()

        asset_one_path = Path("one")
        (assets_directory_path_one / asset_one_path).touch()

        asset_two_path = Path("two")
        (assets_directory_path_two / asset_two_path).touch()

        common_asset_path = Path("common")
        (assets_directory_path_one / common_asset_path).touch()
        (assets_directory_path_two / common_asset_path).touch()

        upstream_one = StaticAssetRepository(assets_directory_path_one)
        upstream_two = StaticAssetRepository(assets_directory_path_two)
        sut = ProxyAssetRepository(upstream_one, upstream_two)

        assert (
            await sut.get(asset_one_path) == assets_directory_path_one / asset_one_path
        )
        assert (
            await sut.get(asset_two_path) == assets_directory_path_two / asset_two_path
        )
        assert (
            await sut.get(common_asset_path)
            == assets_directory_path_one / common_asset_path
        )

    async def test_get__without_upstreams(self) -> None:
        sut = ProxyAssetRepository()
        with pytest.raises(UnknownAsset):
            await sut.get(Path("my-first-asset"))
