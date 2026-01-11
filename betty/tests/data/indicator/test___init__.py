import pathlib

from betty.data.indicator import Path, Url


class TestPath:
    def test_format(self) -> None:
        assert Path(pathlib.Path("my-first-path")).format().endswith("my-first-path")


class TestUrl:
    def test_format(self) -> None:
        assert Url("https://example.com").format() == "https://example.com"
