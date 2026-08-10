from typing import Any

import pytest

from betty.classtools import (
    AlreadyInitialized,
    Init,
    InitClassVar,
    NotYetInitialized,
    Singleton,
)
from betty.importlib import fully_qualified_name


class TestSingleton:
    def test___new__(self) -> None:
        assert Singleton() is Singleton()


class _Init(Init):
    def __repr__(self) -> str:
        return fully_qualified_name(type(self))


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
            == "betty.tests.test_classtools:_Init was unexpectedly not yet initialized"
        )


class TestAlreadyInitialized:
    def test(self) -> None:
        assert (
            str(AlreadyInitialized(_Init()))
            == "betty.tests.test_classtools:_Init was unexpectedly initialized already"
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

    def test_init_class_vars__without_class_vars(self) -> None:
        assert not list(Init.init_class_vars())

    def test_init_class_vars__with_class_var(self) -> None:
        class_var = InitClassVar()

        class _Init(Init):
            my_first_class_var = class_var

        assert list(_Init.init_class_vars()) == [class_var]


class TestInitClassVar:
    def test_pre_init_owner(self) -> None:
        assert not InitClassVar().pre_init_owner(Init())

    def test_post_init_owner(self) -> None:
        assert not InitClassVar().post_init_owner(Init())
