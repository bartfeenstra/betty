from betty.typing import threadsafe


def test_threadsafe() -> None:
    sentinel = object()

    @threadsafe
    def _target() -> object:
        return sentinel

    assert _target() is sentinel
