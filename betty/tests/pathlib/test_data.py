from betty.dirs import ASSETS_DIRECTORY
from betty.pathlib.data import FilePathDefinition


class TestFilePathDefinition:
    def test_load(self) -> None:
        file = ASSETS_DIRECTORY / "app" / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.load(str(file)) == file

    def test_dump(self) -> None:
        file = ASSETS_DIRECTORY / "app" / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.dump(file) == str(file)
