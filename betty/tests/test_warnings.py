import pytest

from betty.warnings import deprecated, BettyDeprecationWarning, deprecate


class TestDeprecate:
    def test(self) -> None:
        with pytest.warns(BettyDeprecationWarning):
            deprecate("oh noes")


class TestDeprecated:
    def test(self) -> None:
        @deprecated("oh noes")
        def _deprecated(sentinel: object) -> object:
            return sentinel

        sentinel = object()
        with pytest.warns(BettyDeprecationWarning):
            actual = _deprecated(sentinel)
        assert actual is sentinel
