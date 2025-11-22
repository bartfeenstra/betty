from betty.typing import internal, private, public, threadsafe


def test_internal() -> None:
    sentinel = object()

    @internal
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


def test_public() -> None:
    sentinel = object()

    @public
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


def test_private() -> None:
    sentinel = object()

    @private
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


def test_threadsafe() -> None:
    sentinel = object()

    @threadsafe
    def _target() -> object:
        return sentinel

    assert _target() is sentinel
