from betty.datas.path import PathDefinition
from betty.dirs import BUILTIN_ASSET_DIRECTORY


class TestPathDefinition:
    def test_load(self) -> None:
        file = BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
        sut = PathDefinition()
        assert sut.porter.load(str(file)) == file

    def test_dump(self) -> None:
        file = BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
        sut = PathDefinition()
        assert sut.porter.dump(file) == str(file)
