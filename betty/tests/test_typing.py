from betty.typing import internal, public, private, threadsafe


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


class TestPrivate:
    def test(self) -> None:
        sentinel = object()

        @private
        def _target() -> object:
            return sentinel

        assert _target() is sentinel


class TestThreadsafe:
    def test(self) -> None:
        sentinel = object()

        @threadsafe
        def _target() -> object:
            return sentinel

        assert _target() is sentinel
