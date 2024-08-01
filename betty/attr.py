"""
The Attr API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import overload, TypeVar, Generic, Self, cast

_InstanceT = TypeVar("_InstanceT")
_ValueT = TypeVar("_ValueT")
_SetT = TypeVar("_SetT")


class Attr(Generic[_InstanceT, _ValueT], ABC):
    """
    A base class for an immutable property-like attribute.
    """

    def __init__(self, attr_name: str):
        self._attr_name = f"_{attr_name}"

    @overload
    def __get__(self, instance: None, _: type[_InstanceT]) -> Self:
        pass

    @overload
    def __get__(self, instance: _InstanceT, _: type[_InstanceT]) -> _ValueT:
        pass

    def __get__(self, instance, _):
        if instance is None:
            return self  # type: ignore[return-value]
        return self.get_attr(instance)

    @abstractmethod
    def new_attr(self, instance: _InstanceT) -> _ValueT:
        """
        Create a new attribute value.
        """
        pass

    def get_attr(self, instance: _InstanceT) -> _ValueT:
        """
        Get the attribute value.
        """
        try:
            return cast(
                _ValueT,
                getattr(instance, self._attr_name),
            )
        except AttributeError:
            value = self.new_attr(instance)
            setattr(instance, self._attr_name, value)
            return value


class MutableAttr(Generic[_InstanceT, _ValueT, _SetT], Attr[_InstanceT, _ValueT]):
    """
    A base class for a mutable property-like attribute.
    """

    def __set__(self, instance: _InstanceT, value: _SetT) -> None:
        self.set_attr(instance, value)

    def __delete__(self, instance: _InstanceT) -> None:
        self.del_attr(instance)

    @abstractmethod
    def set_attr(self, instance: _InstanceT, value: _SetT) -> None:
        """
        Set the attribute value.
        """
        pass

    @abstractmethod
    def del_attr(self, instance: _InstanceT) -> None:
        """
        Delete the attribute value.
        """
        pass
