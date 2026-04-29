from pathlib import Path

from betty.pathlib import resolve_path


def test_resolve_path__with_path() -> None:
    path = Path(__file__)
    assert resolve_path(path) is path


def test_resolve_path__with_str() -> None:
    assert resolve_path(__file__) == Path(__file__)
