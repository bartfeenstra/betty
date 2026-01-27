"""
Object properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, cast, final, overload

from typing_extensions import override

from betty.data import OptionalDefinition
from betty.data.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import LocalizableLike


_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")


class Property(Attr[_ValueGetT], Generic[_ValueGetT, _ValueSetT]):
    """
    An object attribute with a definition.
    """

    _attr_name: str

    def __init__(
        self,
        data: DataDefinition[_ValueGetT] | Data[DataDefinition[_ValueGetT]],
        *,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_ValueGetT], bool] | None = None,
        resolver: Callable[[_ValueSetT | _ValueGetT], _ValueGetT] = passthrough,
        default: Callable[[], _ValueGetT] | None = None,
    ):
        self._data = data
        self._label = label
        self._description = description
        self._attr = AttrDefinition(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
        )
        self._resolver = resolver
        self._default = default

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"

    @override
    @property
    def attr(self) -> AttrDefinition[_ValueGetT]:
        return self._attr

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: Any, owner: type[Any], /) -> _ValueGetT:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = cast(
            _ValueGetT | None,
            getattr(instance, self._attr_name, None),
        )
        if value is None:
            if self._default is None:
                instance_name = fully_qualified_name(type(instance))
                raise PropertyNotInitialized(
                    f"{instance_name}.{self._attr_name[1:]} was never initialized. {instance_name}.__init__() MUST set a value."
                )
            value = self._default()
            setattr(instance, self._attr_name, value)
        return value

    def __set__(self, instance: Any, value: _ValueSetT | _ValueGetT) -> None:
        setattr(instance, self._attr_name, self._resolver(value))


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.data.aggregate.record.object.property.Property`.
    """


@final
class Optional(Attr[_ValueGetT | None], Generic[_ValueGetT, _ValueSetT]):
    """
    Make another property optional, e.g. allow ``None``.
    """

    def __init__(self, required_property: Property[_ValueGetT, _ValueSetT], /):
        self._required_property = required_property

        def _omit_dump(data: _ValueGetT | None) -> bool:
            if data is None:
                return True
            if required_property.attr.omit_dump is None:
                return False
            return required_property.attr.omit_dump(data)

        self._attr = AttrDefinition(
            OptionalDefinition(required_property.attr.data),
            label=required_property.attr.label,
            description=required_property.attr.description,
            omit_load=required_property.attr.omit_load,
            omit_dump=_omit_dump,
        )

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"
        self._required_property.__set_name__(owner, name)

    @override
    @property
    def attr(self) -> AttrDefinition[_ValueGetT | None]:
        return self._attr

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: Any, owner: type[Any], /) -> _ValueGetT | None:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return self._required_property.__get__(instance, owner)
        except PropertyNotInitialized:
            self.__set__(instance, None)
            return None

    def __set__(self, instance: Any, value: _ValueSetT | _ValueGetT | None) -> None:
        if value is None:
            self.__delete__(instance)
        else:
            self._required_property.__set__(instance, value)

    def __delete__(self, instance: Any) -> None:
        setattr(instance, self._attr_name, None)
