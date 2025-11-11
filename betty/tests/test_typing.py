import pickle

import pytest

from betty.typing import (
    internal,
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
