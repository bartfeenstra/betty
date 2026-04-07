"""
Object properties.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self, cast, final, overload, override

from betty.data import OptionalDefinition
from betty.data.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class _Property[ValueGetT, ValueSetT](Attr[ValueGetT], ABC):
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
    def get(self, instance: Any) -> ValueGetT:
        """
        Get the property value from the instance.
        """

    def set(self, instance: Any, value: ValueSetT | ValueGetT) -> ValueGetT:
        """
        Set the value on the instance.
        """
        resolved_value = self._resolver(value)
        setattr(instance, self._attr_name, resolved_value)
        return resolved_value


class Property[ValueGetT, ValueSetT](_Property[ValueGetT, ValueSetT]):
    """
    An object attribute with a definition.
    """

    def __init__(
        self,
        data: DataDefinition[ValueGetT] | type[Data[DataDefinition[ValueGetT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[ValueGetT], bool] | None = None,
        resolver: Callable[[ValueSetT | ValueGetT], ValueGetT] = passthrough,
        default: Callable[[], ValueGetT] | None = None,
    ):
        super().__init__(
            AttrDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            ),
            resolver=resolver,
        )
        self._data = data
        self._label = label
        self._description = description
        self._default = default

    @override
    def get(self, instance: Any) -> ValueGetT:
        value = cast(
            ValueGetT | Void,
            getattr(instance, self._attr_name, Void),
        )
        if value is Void:
            if self._default is None:
                instance_name = fully_qualified_name(type(instance))
                raise PropertyNotInitialized(
                    f"{instance_name}.{self._attr_name[1:]} was never initialized. Either provide a default when initializing the property, or make {instance_name}.__init__() set a value."
                )
            value = self._default()
            setattr(instance, self._attr_name, value)
        return value  # ty:ignore[invalid-return-type]


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.property.Property`.
    """


@final
class Optional[ValueGetT, ValueSetT](_Property[ValueGetT | None, ValueSetT | None]):
    """
    Make another property optional, e.g. allow ``None``.
    """

    def __init__(self, required_property: Property[ValueGetT, ValueSetT], /):
        def _omit_dump(data: ValueGetT | None) -> bool:
            if data is None:
                return True
            if required_property.attr.omit_dump is None:
                return False
            return required_property.attr.omit_dump(data)

        super().__init__(
            AttrDefinition(
                OptionalDefinition(required_property.attr.data),
                label=required_property.attr.label,
                description=required_property.attr.description,
                omit_load=required_property.attr.omit_load,
                omit_dump=_omit_dump,
            )
        )
        self._required_property = required_property

    def __set_name__(self, owner: type[Any], name: str) -> None:
        super().__set_name__(owner, name)
        self._required_property.__set_name__(owner, name)

    @override
    def get(self, instance: Any) -> ValueGetT | None:
        try:
            return self._required_property.get(instance)
        except PropertyNotInitialized:
            return self.set(instance, None)

    @override
    def set(self, instance: Any, value: ValueSetT | ValueGetT | None) -> ValueGetT:
        if value is None:
            return super().set(instance, value)
        return self._required_property.set(instance, value)

    def __delete__(self, instance: Any) -> None:
        self.delete(instance)

    def delete(self, instance: Any) -> None:
        """
        Delete the value from the instance.
        """
        self.set(instance, None)
