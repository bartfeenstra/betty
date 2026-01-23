from pathlib import Path

import pytest

from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.exception import HumanFacingException
from betty.pathlib import FilePathDefinition


class TestFilePathDefinition:
    def test_load(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.load(str(file_path)) == file_path

    def test_load__with_non_existent_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non-existent-file"
        sut = FilePathDefinition()
        with pytest.raises(HumanFacingException):
            sut.load(str(file_path))

    def test_dump(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.dump(file_path) == str(file_path)
