from pathlib import Path

import pytest

from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.error import FileNotFound
from betty.pathlib import FilePathDefinition
from betty.service.level import UNIVERSE


class TestFilePathDefinition:
    def test_load(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.load(str(file_path)) == file_path

    def test_dump(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.dump(file_path) == str(file_path)

    async def test_hydrate(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        await sut.hydrate(UNIVERSE, str(file_path))

    async def test_hydrate__with_non_existent_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non-existent-file"
        sut = FilePathDefinition()
        with pytest.raises(FileNotFound):
            await sut.hydrate(UNIVERSE, file_path)
