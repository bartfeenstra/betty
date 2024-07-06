from pathlib import Path

from aiofiles.tempfile import TemporaryDirectory

from betty.assets import AssetRepository


class TestAssetRepository:
    async def test_assets_directory_paths(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                sut = AssetRepository(source_path_1, source_path_2)
                assert sut.assets_directory_paths == (source_path_1, source_path_2)

    async def test___getitem___with_override(
        self,
    ) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_1 / "apples").touch()
                (source_path_2 / "apples").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert sut[Path("apples")] == source_path_1 / "apples"

    async def test___getitem___without_override(
        self,
    ) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_1 / "apples").touch()
                (source_path_2 / "oranges").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert sut[Path("oranges")] == source_path_2 / "oranges"

    async def test_walk_with_override(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_1 / "apples").touch()
                (source_path_2 / "apples").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert set(sut.walk()) == {Path("apples")}

    async def test_walk_without_override(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_1 / "apples").touch()
                (source_path_2 / "oranges").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert set(sut.walk()) == {
                    Path("apples"),
                    Path("oranges"),
                }

    async def test_walk_with_override_with_filter(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            (source_path_1 / "fruits").mkdir()
            (source_path_1 / "vegetables").mkdir()
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_2 / "fruits").mkdir()
                (source_path_2 / "vegetables").mkdir()
                (source_path_1 / "fruits" / "apples").touch()
                (source_path_2 / "fruits" / "apples").touch()
                (source_path_1 / "vegetables" / "peppers").touch()
                (source_path_2 / "vegetables" / "peppers").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert set(sut.walk(Path("fruits"))) == {Path("fruits") / "apples"}

    async def test_walk_without_override_with_filter(self) -> None:
        async with TemporaryDirectory() as source_path_str_1:
            source_path_1 = Path(source_path_str_1)
            (source_path_1 / "fruits").mkdir()
            (source_path_1 / "vegetables").mkdir()
            async with TemporaryDirectory() as source_path_str_2:
                source_path_2 = Path(source_path_str_2)
                (source_path_2 / "fruits").mkdir()
                (source_path_2 / "vegetables").mkdir()
                (source_path_1 / "fruits" / "apples").touch()
                (source_path_2 / "fruits" / "oranges").touch()
                (source_path_1 / "vegetables" / "peppers").touch()
                (source_path_2 / "vegetables" / "oranges").touch()
                sut = AssetRepository(source_path_1, source_path_2)
                assert set(sut.walk(Path("fruits"))) == {
                    Path("fruits") / "apples",
                    Path("fruits") / "oranges",
                }
