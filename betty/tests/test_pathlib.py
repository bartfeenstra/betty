from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.pathlib import FilePathDefinition


class TestFilePathDefinition:
    def test_load(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.load(str(file_path)) == file_path

    def test_dump(self) -> None:
        file_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.dump(file_path) == str(file_path)
