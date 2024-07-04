from betty.typing import internal, public


class TestInternal:
    def test(self) -> None:
        sentinel = object()

        @internal
        def _target() -> object:
            return sentinel

        assert _target() is sentinel


class TestPublic:
    def test(self) -> None:
        sentinel = object()

        @public
        def _target() -> object:
            return sentinel

        assert _target() is sentinel
