from pathlib import Path

import aiofiles
from aiofiles.tempfile import TemporaryDirectory

from betty.fs import iterfiles


class TestIterfiles:
    async def test_iterfiles(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            working_subdirectory_path = working_directory_path / "subdir"
            working_subdirectory_path.mkdir()
            async with aiofiles.open(working_directory_path / "rootfile", "a"):
                pass
            async with aiofiles.open(working_directory_path / ".hiddenrootfile", "a"):
                pass
            async with aiofiles.open(working_subdirectory_path / "subdirfile", "a"):
                pass
            actual = [
                str(actualpath)[len(str(working_directory_path)) + 1 :]
                async for actualpath in iterfiles(working_directory_path)
            ]
        expected = {
            ".hiddenrootfile",
            "rootfile",
            str(Path("subdir") / "subdirfile"),
        }
        assert expected == set(actual)
