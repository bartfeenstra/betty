from collections.abc import Iterable
from typing import Any, override

import pytest

from betty.classtools import (
    Object,
    ObjectAlreadyInitialized,
    ObjectClassVar,
    ObjectNotYetInitialized,
)
from betty.importlib import fully_qualified_name


class _Object(Object):
    def __repr__(self) -> str:
        return fully_qualified_name(self)


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


class TestType:
    def test___new____without_slots_creation(self) -> None:
        class _Object(Object):
            pass

        assert not hasattr(_Object, "__slots__")

    def test___new____without_slots(self) -> None:
        class _Object(Object, slots=True):
            pass

        assert _Object.__slots__ == ()  # ty: ignore[unresolved-attribute]

    def test___new____with_explicit_slots_as_tuple(self) -> None:
        class _Object(Object, slots=True):
            __slots__ = ("my_explicit_slot",)

        assert _Object.__slots__ == ("my_explicit_slot",)

    def test___new____with_explicit_slots_as_str(self) -> None:
        class _Object(Object, slots=True):
            __slots__ = "my_explicit_slot"  # noqa: PLC0205

        assert _Object.__slots__ == ("my_explicit_slot",)

    def test___new____with_declared_slots(self) -> None:
        class _Object(Object, slots=True):
            @override
            @classmethod
            def _slots(cls) -> Iterable[str]:
                yield "my_declared_slot"

        assert _Object.__slots__ == ("my_declared_slot",)  # ty: ignore[unresolved-attribute]

    def test___new____with_explicit_and_declared_slots(self) -> None:
        class _Object(Object, slots=True):
            __slots__ = ("my_explicit_slot",)

            @override
            @classmethod
            def _slots(cls) -> Iterable[str]:
                yield "my_declared_slot"

        assert _Object.__slots__ == ("my_declared_slot", "my_explicit_slot")


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


class TestObjectClassVar:
    def test_pre_init_owner(self) -> None:
        ObjectClassVar().pre_init_owner(Object())

    def test_post_init_owner(self) -> None:
        ObjectClassVar().post_init_owner(Object())
