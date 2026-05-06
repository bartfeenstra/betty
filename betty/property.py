"""
Object properties.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self, cast, final, overload, override

from betty.data import OptionalDefinition
from betty.datas.aggregate.record.object import Attr, AttrDefinition
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class Property[ValueGetT, ValueSetT](Attr[ValueGetT], ABC):
    """
    An instance property backed by a data definition.
    """

    __name: str

    def __init__(self, attr: AttrDefinition[ValueGetT], /):
        self.__attr = attr

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.__name = f"_{name}"

    @final
    @override
    @property
    def attr(self) -> AttrDefinition[ValueGetT]:
        return self.__attr

    @final
    @property
    def name(self) -> str:
        """
        The property/attribute name.
        """
        return self.__name

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: Any, owner: type[Any] | None = None, /) -> ValueGetT:
        pass

    @final
    def __get__(self, instance, owner=None, /):
        if instance is None:
            return self
        return self.get(instance)

    @final
    def __set__(self, instance: Any, value: ValueSetT | ValueGetT) -> None:
        self.set(instance, value)

    @abstractmethod
    def get(self, instance: Any, /) -> ValueGetT:
        """
        Get the property value from the instance.
        """

    @abstractmethod
    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        """
        Set the value on the instance.
        """

    @final
    def getter[GetterValueGetT](
        self, getter: Callable[[Any, ValueGetT], GetterValueGetT], /
    ) -> Property[GetterValueGetT, ValueSetT]:
        """
        Return a new property with the given getter.
        """
        return GetterProperty(self, getter)

    @final
    def __call__[GetterValueGetT](
        self, getter: Callable[[Any, ValueGetT], GetterValueGetT], /
    ) -> Property[GetterValueGetT, ValueSetT]:
        """
        Return a new property with the given getter.
        """
        return self.getter(getter)

    @final
    def setter[SetterValueSetT](
        self, setter: Callable[[Any, ValueSetT], SetterValueSetT], /
    ) -> Property[ValueGetT, SetterValueSetT]:
        """
        Return a new property with the given setter.
        """
        return SetterProperty(self, setter)

    @final
    def default(
        self, default: Callable[[Any], ValueSetT], /
    ) -> Property[ValueGetT, ValueSetT]:
        """
        Return a new property with the given default value factory.
        """
        return DefaultProperty(self, default)


class ProxyProperty[ValueGetT, ValueSetT](Property[ValueGetT, ValueSetT]):
    """
    A property that proxies everything to another wrapped property.
    """

    def __init__(self, wrapped: Property[ValueGetT, ValueSetT], /):
        super().__init__(wrapped.attr)
        self._wrapped = wrapped

    @override
    def __set_name__(self, owner: type[Any], name: str) -> None:
        super().__set_name__(owner, name)
        self._wrapped.__set_name__(owner, name)

    @override
    def get(self, instance: Any, /) -> ValueGetT:
        return self._wrapped.get(instance)

    @override
    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        return self._wrapped.set(instance, value)


@final
class GetterProperty[ValueGetT, ValueSetT](ProxyProperty[ValueGetT, ValueSetT]):
    """
    Decorate a property with a getter callable.
    """

    def __init__[WrappedValueGetT](
        self,
        wrapped: Property[WrappedValueGetT, ValueSetT],
        getter: Callable[[Any, WrappedValueGetT], ValueGetT],
        /,
    ):
        super().__init__(wrapped)
        self._getter = getter

    @override
    def get(self, instance: Any, /) -> ValueGetT:
        return self._getter(instance, self._wrapped.get(instance))


@final
class SetterProperty[ValueGetT, ValueSetT](ProxyProperty[ValueGetT, ValueSetT]):
    """
    Decorate a property with a setter callable.
    """

    def __init__[WrappedValueSetT](
        self,
        wrapped: Property[ValueGetT, WrappedValueSetT],
        setter: Callable[[Any, ValueSetT], WrappedValueSetT],
        /,
    ):
        super().__init__(wrapped)
        self._setter = setter

    @override
    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        return self._wrapped.set(instance, self._setter(instance, value))


@final
class DefaultProperty[ValueGetT, ValueSetT](ProxyProperty[ValueGetT, ValueSetT]):
    """
    Decorate a property with a default value factory.
    """

    def __init__(
        self,
        wrapped: Property[ValueGetT, ValueSetT],
        default: Callable[[Any], ValueGetT],
        /,
    ):
        super().__init__(wrapped)
        self._default = default

    @override
    def get(self, instance: Any, /) -> ValueGetT:
        # @todo This needs locking!!!
        # @todo Use LazyReCallable? NO! Because that caches the result, and we must proxy!
        # @todo
        try:
            return self._wrapped.get(instance)
        except PropertyNotInitialized:
            value = self._default(instance)
            setattr(instance, self.name, value)
        return value


class AttrProperty[ValueGetT, ValueSetT](Property[ValueGetT, ValueSetT]):
    """
    A property that stores its value in an instance attribute.
    """

    def __init__(
        self,
        data: DataDefinition[ValueGetT] | type[Data[DataDefinition[ValueGetT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[ValueGetT], bool] | None = None,
    ):
        super().__init__(
            AttrDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            )
        )
        self._data = data

    @override
    def get(self, instance: Any, /) -> ValueGetT:
        value = cast(
            ValueGetT | Void,
            getattr(instance, self.name, Void),
        )
        if value is Void:
            instance_name = fully_qualified_name(type(instance))
            raise PropertyNotInitialized(
                f"{instance_name}.{self.name[1:]} was never initialized."
            )
        return value  # ty:ignore[invalid-return-type]

    @override
    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        setattr(instance, self.name, value)
        return value


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.property.Property`.
    """


@final
class Optional[ValueGetT, ValueSetT](Property[ValueGetT | None, ValueSetT | None]):
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
    def get(self, instance: Any, /) -> ValueGetT | None:
        try:
            return self._required_property.get(instance)
        except PropertyNotInitialized:
            return self.set(instance, None)

    @override
    def set(self, instance: Any, value: ValueSetT | None, /) -> ValueGetT | None:
        if value is None:
            return super().set(instance, value)
        return self._required_property.set(instance, value)

    def __delete__(self, instance: Any) -> None:
        self.delete(instance)

    def delete(self, instance: Any, /) -> None:
        """
        Delete the value from the instance.
        """
        self.set(instance, None)
