from typing import Any

import pytest

from betty.classtools import (
    Object,
    ObjectAlreadyInitialized,
    ObjectClassVar,
    ObjectNotYetInitialized,
    Singleton,
)
from betty.importlib import fully_qualified_name


class TestSingleton:
    def test___new__(self) -> None:
        assert Singleton() is Singleton()


class _Object(Object):
    def __repr__(self) -> str:
        return fully_qualified_name(type(self))


class _ObjectWithArg(_Object):
    def __init__(self, arg: Any, /):
        super().__init__()


class _ObjectWithKwarg(_Object):
    def __init__(self, *, kwarg: Any):
        super().__init__()


class _ObjectWithArgAndKwarg(_Object):
    def __init__(self, arg: Any, /, *, kwarg: Any):
        super().__init__()


class TestObjectNotYetInitialized:
    def test(self) -> None:
        assert (
            str(ObjectNotYetInitialized(_Object()))
            == "betty.tests.test_classtools:_Object was unexpectedly not yet initialized"
        )


class TestObjectAlreadyInitialized:
    def test(self) -> None:
        assert (
            str(ObjectAlreadyInitialized(_Object()))
            == "betty.tests.test_classtools:_Object was unexpectedly initialized already"
        )


class TestObject:
    def test___new__(self) -> None:
        assert Object().is_initialized

    def test___new____with_subclass(self) -> None:
        assert _Object().is_initialized

    def test___new____with_subclass_with_init_arg(self) -> None:
        assert _ObjectWithArg("Arg").is_initialized

    def test___new____with_subclass_with_init_kwarg(self) -> None:
        assert _ObjectWithKwarg(kwarg="Kwarg").is_initialized

    def test___new____with_subclass_with_init_arg_and_kwarg(self) -> None:
        assert _ObjectWithArgAndKwarg("Arg", kwarg="Kwarg").is_initialized

    def test_is_initialized(self) -> None:
        class _Object(Object):
            def __init__(self):
                assert not self.is_initialized

        assert _Object().is_initialized

    def test_assert_initialized(self) -> None:
        class _Object(Object):
            def __init__(self):
                with pytest.raises(ObjectNotYetInitialized):
                    self.assert_initialized()

        _Object().assert_initialized()

    def test_assert_not_initialized(self) -> None:
        class _Object(Object):
            def __init__(self):
                self.assert_not_initialized()

        with pytest.raises(ObjectAlreadyInitialized):
            _Object().assert_not_initialized()

    def test_init_class_vars__without_class_vars(self) -> None:
        assert not list(Object.init_class_vars())

    def test_init_class_vars__with_class_var(self) -> None:
        class_var = ObjectClassVar()

        class _Object(Object):
            my_first_class_var = class_var

        assert list(_Object.init_class_vars()) == [class_var]


class TestObjectClassVar:
    def test_pre_init_owner(self) -> None:
        assert not ObjectClassVar().pre_init_owner(Object())

    def test_post_init_owner(self) -> None:
        assert not ObjectClassVar().post_init_owner(Object())
