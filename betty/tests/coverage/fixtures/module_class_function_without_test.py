"""Provide fixtures for a source method without a matching test method."""


class Src:
    """Provide a fixture source method."""

    def src(self) -> None:
        raise NotImplementedError


class TestSrc:
    pass  # pragma: no cover
