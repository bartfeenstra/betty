"""
Object attribute tools.
"""

from abc import abstractmethod
from typing import Any, Generic, Self, TypeVar, cast, final, overload

from typing_extensions import override

from betty.importlib import fully_qualified_name
from betty.typing import internal

_ValueT = TypeVar("_ValueT")
_OwnerT = TypeVar("_OwnerT")


class _Attr(Generic[_ValueT]):
    _attr_name: str

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: _OwnerT, owner: type[_OwnerT], /) -> _ValueT:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._check_get(instance, self._get(instance))

    def _get(self, instance: object, /) -> _ValueT | None:
        return cast(
            _ValueT | None,
            getattr(instance, self._attr_name, None),
        )

    @abstractmethod
    def _check_get(self, instance: object, value: _ValueT | None, /) -> _ValueT:
        pass


@final
class AttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.attr.RequiredAttr`.
    """


@internal
class RequiredAttr(_Attr[_ValueT]):
    """
    A base class for descriptors with required values.
    """

    @override
    def _check_get(self, instance: object, value: _ValueT | None, /) -> _ValueT:
        if value is None:
            instance_name = fully_qualified_name(type(instance))
            raise AttrNotInitialized(
                f"{instance_name}.{self._attr_name[1:]} was never initialized. {instance_name}.__init__() MUST set a value."
            )
        return value


@internal
class OptionalAttr(_Attr[_ValueT | None]):
    """
    A base class for descriptors with optional values.
    """

    @override
    def _check_get(self, instance: object, value: _ValueT | None, /) -> _ValueT | None:
        return value
