from pathlib import Path

import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.assets import AssetRepository


class TestAssetRepository:
    @pytest.fixture
    async def sut(self, tmp_path: Path) -> tuple[AssetRepository, Path, Path]:
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
            AssetRepository(source_path_1, source_path_2),
            source_path_1,
            source_path_2,
        )

    async def test_assets_directory_paths(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                sut = AssetRepository(source_path_1, source_path_2)
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
