from betty.dirs import BUILTIN_ASSET_DIRECTORY
from betty.pathlib.data import FilePathDefinition


class TestFilePathDefinition:
    def test_load(self) -> None:
        file = BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.load(str(file)) == file

    def test_dump(self) -> None:
        file = BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
        sut = FilePathDefinition()
        assert sut.porter.dump(file) == str(file)
