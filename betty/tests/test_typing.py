from betty.typing import (
    internal,
    public,
    private,
    threadsafe,
    not_void,
    Void,
    pickleable,
    processsafe,
)


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


class TestPickleable:
    def test(self) -> None:
        sentinel = object()

        @pickleable
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


class TestProcesssafe:
    def test(self) -> None:
        sentinel = object()

        @processsafe
        def _target() -> object:
            return sentinel

        assert _target() is sentinel


class TestNotVoid:
    def test_with_void(self) -> None:
        assert not not_void(Void)

    def test_without_void(self) -> None:
        assert not_void(123)
