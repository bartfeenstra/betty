"""
Object attributes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self, final, overload, override

from betty.datas.aggregate.record.object import Attr as DataAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.functools import passthrough

if TYPE_CHECKING:
    from collections.abc import Callable


class Attr[ValueGetT, ValueSetT](DataAttr[ValueGetT], ABC):
    """
    An object attribute with a definition.
    """

    _attr_name: str

    def __init__(
        self,
        attr: AttrDefinition[ValueGetT],
        *,
        resolver: Callable[[ValueSetT | ValueGetT], ValueGetT] = passthrough,
    ):
        self._attr = attr
        self._resolver = resolver

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"

    @final
    @override
    @property
    def attr(self) -> AttrDefinition[ValueGetT]:
        return self._attr

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: Any, owner: type[Any] | None = None, /) -> ValueGetT:
        pass

    def __get__(self, instance, owner=None, /):
        if instance is None:
            return self
        return self.get(instance)

    def __set__(self, instance: Any, value: ValueSetT | ValueGetT) -> None:
        self.set(instance, value)

    @abstractmethod
    def get(self, instance: Any, /) -> ValueGetT:
        """
        Get the attribute value from the instance.
        """

    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        """
        Set the value on the instance.
        """
        resolved_value = self._resolver(value)
        setattr(instance, self._attr_name, resolved_value)
        return resolved_value


@final
class AttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.attr.Attr`.
    """
