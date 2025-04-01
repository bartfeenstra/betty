import pickle

import pytest

from betty.typing import (
    Sentinel,
    Void,
    internal,
    not_void,
    pickleable,
    private,
    processsafe,
    public,
    threadsafe,
    unpickleable,
)


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


def test_pickleable() -> None:
    sentinel = object()

    @pickleable
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


@unpickleable
class _Unpickleable:
    def __call__(self, sentinel: object) -> object:
        return sentinel


def test_unpickleable() -> None:
    sentinel = object()

    sut = _Unpickleable()
    assert sut(sentinel) is sentinel
    with pytest.raises(RuntimeError):
        pickle.dumps(sut)


def test_threadsafe() -> None:
    sentinel = object()

    @threadsafe
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


def test_processsafe() -> None:
    sentinel = object()

    @processsafe
    def _target() -> object:
        return sentinel

    assert _target() is sentinel


class TestSentinel:
    def test___new__(self) -> None:
        with pytest.raises(TypeError):
            Sentinel()


def test_not_void__with_void() -> None:
    assert not not_void(Void)


def test_not_void__without_void() -> None:
    assert not_void(123)
