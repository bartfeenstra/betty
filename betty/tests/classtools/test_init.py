from typing import Any

import pytest

from betty.classtools.init import (
    AlreadyInitialized,
    Init,
    InitClassVar,
    NotYetInitialized,
    init,
)
from betty.importlib import fully_qualified_name


class _Init(Init):
    def __repr__(self) -> str:
        return fully_qualified_name(self)


class _InitWithArg(_Init):
    def __init__(self, arg: Any, /):
        super().__init__()


class _InitWithKwarg(_Init):
    def __init__(self, *, kwarg: Any):
        super().__init__()


class _InitWithArgAndKwarg(_Init):
    def __init__(self, arg: Any, /, *, kwarg: Any):
        super().__init__()


class TestNotYetInitialized:
    def test(self) -> None:
        assert (
            str(NotYetInitialized(_Init()))
            == "betty.tests.classtools.test_init:_Init was unexpectedly not yet initialized"
        )


class TestAlreadyInitialized:
    def test(self) -> None:
        assert (
            str(AlreadyInitialized(_Init()))
            == "betty.tests.classtools.test_init:_Init was unexpectedly initialized already"
        )


class TestInit:
    def test___new__(self) -> None:
        assert Init().is_initialized

    def test___new____with_subclass(self) -> None:
        assert _Init().is_initialized

    def test___new____with_subclass_with_init_arg(self) -> None:
        assert _InitWithArg("Arg").is_initialized

    def test___new____with_subclass_with_init_kwarg(self) -> None:
        assert _InitWithKwarg(kwarg="Kwarg").is_initialized

    def test___new____with_subclass_with_init_arg_and_kwarg(self) -> None:
        assert _InitWithArgAndKwarg("Arg", kwarg="Kwarg").is_initialized

    def test_is_initialized(self) -> None:
        class _Init(Init):
            def __init__(self):
                assert not self.is_initialized

        assert _Init().is_initialized

    def test_assert_initialized(self) -> None:
        class _Init(Init):
            def __init__(self):
                with pytest.raises(NotYetInitialized):
                    self.assert_initialized()

        _Init().assert_initialized()

    def test_assert_not_initialized(self) -> None:
        class _Init(Init):
            def __init__(self):
                self.assert_not_initialized()

        with pytest.raises(AlreadyInitialized):
            _Init().assert_not_initialized()


class TestInitClassVar:
    def test_pre_init_owner(self) -> None:
        InitClassVar().pre_init_owner(Init())

    def test_post_init_owner(self) -> None:
        InitClassVar().post_init_owner(Init())


def test_init__minimal() -> None:
    @init
    class _Cls(Init):
        pass

    assert isinstance(_Cls(), _Cls)


# @todo - With class's own __init__()
# @todo - With inherited __init__()
# @todo - With inherited __init__() already decorated with @init
# @todo
# @todo
def test_init() -> None:
    raise NotImplementedError
