from betty.data.indicator import AnyIndex, AnyKey, Path, Url


class TestAnyIndex:
    def test_format(self) -> None:
        assert AnyIndex().format()


class TestAnyKey:
    def test_format(self) -> None:
        assert AnyKey().format()


class TestPath:
    def test_format(self) -> None:
        assert Path("my-first-path").format().endswith("my-first-path")


class TestUrl:
    def test_format(self) -> None:
        assert Url("https://example.com").format() == "https://example.com"
