from typing import Any

import pytest

from betty.classtools.co_op import (
    AlreadyInitialized,
    CoOp,
    CoOpClassVar,
    NotYetInitialized,
)
from betty.importlib import fully_qualified_name


class _CoOp(CoOp):
    def __repr__(self) -> str:
        return fully_qualified_name(self)


class _CoOpWithArg(_CoOp):
    def __init__(self, arg: Any, /):
        super().__init__()


class _CoOpWithKwarg(_CoOp):
    def __init__(self, *, kwarg: Any):
        super().__init__()


class _CoOpWithArgAndKwarg(_CoOp):
    def __init__(self, arg: Any, /, *, kwarg: Any):
        super().__init__()


class TestNotYetInitialized:
    def test(self) -> None:
        assert (
            str(NotYetInitialized(_CoOp()))
            == "betty.tests.classtools.test_co_op:_CoOp was unexpectedly not yet initialized"
        )


class TestAlreadyInitialized:
    def test(self) -> None:
        assert (
            str(AlreadyInitialized(_CoOp()))
            == "betty.tests.classtools.test_co_op:_CoOp was unexpectedly initialized already"
        )


class TestCoOp:
    def test___new__(self) -> None:
        assert CoOp().is_initialized

    def test___new____with_subclass(self) -> None:
        assert _CoOp().is_initialized

    def test___new____with_subclass_with_init_arg(self) -> None:
        assert _CoOpWithArg("Arg").is_initialized

    def test___new____with_subclass_with_init_kwarg(self) -> None:
        assert _CoOpWithKwarg(kwarg="Kwarg").is_initialized

    def test___new____with_subclass_with_init_arg_and_kwarg(self) -> None:
        assert _CoOpWithArgAndKwarg("Arg", kwarg="Kwarg").is_initialized

    def test_is_initialized(self) -> None:
        class _CoOp(CoOp):
            def __init__(self):
                assert not self.is_initialized

        assert _CoOp().is_initialized

    def test_assert_initialized(self) -> None:
        class _CoOp(CoOp):
            def __init__(self):
                with pytest.raises(NotYetInitialized):
                    self.assert_initialized()

        _CoOp().assert_initialized()

    def test_assert_not_initialized(self) -> None:
        class _CoOp(CoOp):
            def __init__(self):
                self.assert_not_initialized()

        with pytest.raises(AlreadyInitialized):
            _CoOp().assert_not_initialized()


class TestCoOpClassVar:
    def test_pre_init_owner(self) -> None:
        CoOpClassVar().pre_init_owner(CoOp())

    def test_post_init_owner(self) -> None:
        CoOpClassVar().post_init_owner(CoOp())
