from pathlib import Path

from betty.pathlib import Extension, resolve_path


def test_resolve_path__with_path() -> None:
    path = Path(__file__)
    assert resolve_path(path) is path


def test_resolve_path__with_str() -> None:
    assert resolve_path(__file__) == Path(__file__)


class TestExtension:
    def test(self) -> None:
        assert Extension("my.first.suffix") == ".suffix"
        assert Extension(Path("my.first.suffix")) == ".suffix"
        assert Extension("My.First.Suffix") == ".suffix"
        assert Extension(".suffix") == ".suffix"
        assert Extension("suffix") == ".suffix"
