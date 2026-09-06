"""Provide fixtures for a source method with a matching test method."""

from betty.typing import Unreachable


class Src:
    """Provide a fixture source class."""

    def src(self) -> None:
        raise Unreachable


class TestSrc:
    def test_src(self) -> None:
        pass  # pragma: no cover
