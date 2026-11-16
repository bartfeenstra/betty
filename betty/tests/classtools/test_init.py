from typing import Any, override

import pytest

from betty.classtools.init import (
    AlreadyInitialized,
    Init,
    InitClassVar,
    NotYetInitialized,
)
from betty.importlib import fully_qualified_name


class _Init(Init):
    def __repr__(self) -> str:
        return fully_qualified_name(self)


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


class _Owner(Init):
    pre_init_class_var: bool
    post_init_class_var: bool


class _InitClassVar(InitClassVar[_Owner]):
    @override
    def pre_init_owner(self, owner: _Owner, /) -> None:
        owner.pre_init_class_var = True

    def post_init_owner(self, owner: _Owner, /) -> None:
        owner.post_init_class_var = True


class TestInit:
    def test___init_subclass___wraps(self) -> None:
        tracker = []

        class _WrapsInit(_Init):
            def __init__(self, arg: Any, /, *, kwarg: Any):
                super().__init__()
                assert arg == "Arg"
                assert kwarg == "Kwarg"
                tracker.append("__init__")

            @override
            def pre_init(self) -> None:
                tracker.append("pre_init")

            @override
            def post_init(self) -> None:
                tracker.append("post_init")

        sut = _WrapsInit("Arg", kwarg="Kwarg")
        assert sut.is_initialized
        assert tracker == ["pre_init", "__init__", "post_init"]

    def test___init_subclass___override(self) -> None:
        tracker = []

        class _WrapsInit(_Init):
            def __init__(self, arg: Any, /, *, kwarg: Any):
                super().__init__()
                assert arg == "Arg"
                assert kwarg == "Kwarg"
                tracker.append("__init__")

        class _OverrideWrapsInit(_WrapsInit):
            @override
            def pre_init(self) -> None:
                tracker.append("pre_init")

            @override
            def post_init(self) -> None:
                tracker.append("post_init")

        sut = _OverrideWrapsInit("Arg", kwarg="Kwarg")
        assert sut.is_initialized
        assert tracker == ["pre_init", "__init__", "post_init"]

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

    def test_pre_init__without_init_class_vars(self) -> None:
        _Owner()

    def test_pre_init__with_init_class_vars(self) -> None:
        class __Owner(_Owner):
            my_first_init_class_var = _InitClassVar()

            def __init__(self):
                assert self.pre_init_class_var

        sut = __Owner()
        assert sut.post_init_class_var

    def test_post_init__without_init_class_vars(self) -> None:
        _Init()

    def test_post_init__with_init_class_vars(self) -> None:
        class __Owner(_Owner):
            my_first_init_class_var = _InitClassVar()

            def __init__(self):
                assert self.pre_init_class_var

        sut = __Owner()
        assert sut.post_init_class_var


class TestInitClassVar:
    def test_pre_init_owner(self) -> None:
        InitClassVar().pre_init_owner(object())

    def test_post_init_owner(self) -> None:
        InitClassVar().post_init_owner(object())
