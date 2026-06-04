from betty.datas.path import PathDefinition
from betty.dirs import builtin_asset_directory


class TestPathDefinition:
    def test_load(self) -> None:
        file = builtin_asset_directory / "public" / "static" / "betty-512x512.png"
        sut = PathDefinition()
        assert sut.porter.load(str(file)) == file

    def test_dump(self) -> None:
        file = builtin_asset_directory / "public" / "static" / "betty-512x512.png"
        sut = PathDefinition()
        assert sut.porter.dump(file) == str(file)
