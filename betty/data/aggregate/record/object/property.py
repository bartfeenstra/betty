"""
Object properties.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, MutableMapping, MutableSequence
from typing import TYPE_CHECKING, Any, Self, cast, final, overload, override

from betty.data import OptionalDefinition
from betty.data.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

    from betty.collection.keyed import MutableKeyedCollection
    from betty.data import Data, DataDefinition
    from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
    from betty.data.aggregate.collection.mapping import MappingDefinition
    from betty.data.aggregate.collection.sequence import SequenceDefinition
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
    def __get__(self, instance: Any, owner: type[Any], /) -> ValueGetT:
        pass

    def __get__(self, instance, owner):
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
    Raised when a class failed to initialize a value for a :py:class:`betty.data.aggregate.record.object.property.Property`.
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


class MappingProperty[MutableMappingT: MutableMapping[Any, Any], ValueSetT](
    Property[MutableMappingT, ValueSetT]
):
    """
    A property that contains a :py:class:`collections.abc.MutableMapping`.
    """

    _data: MappingDefinition[MutableMappingT]

    def __init__(
        self,
        data: Intersection[DataDefinition[MutableMappingT], MappingDefinition]
        | Data[Intersection[DataDefinition[MutableMappingT], MappingDefinition]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableMappingT], bool] | None = None,
        default: Callable[[], Mapping] = dict,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._default_values = default

    def _new_default(self) -> MutableMappingT:
        new = self._data.new()
        new.update(self._default_values())
        return new

    @override
    def set(self, instance: Any, value: ValueSetT | MutableMappingT) -> MutableMappingT:
        data = self.get(instance)
        data.clear()
        data.update(self._resolver(value))
        return data


class SequenceProperty[MutableSequenceT: MutableSequence[Any], ValueSetT](
    Property[MutableSequenceT, ValueSetT]
):
    """
    A property that contains a :py:class:`collections.abc.MutableSequence`.
    """

    _data: SequenceDefinition[MutableSequenceT]

    def __init__(
        self,
        data: Intersection[DataDefinition[MutableSequenceT], SequenceDefinition]
        | Data[Intersection[DataDefinition[MutableSequenceT], SequenceDefinition]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableSequenceT], bool] | None = None,
        resolver: Callable[
            [ValueSetT | Iterable[ValueSetT]], Iterable[ValueSetT]
        ] = passthrough,
        default: Callable[[], ValueSetT | Iterable[ValueSetT]] = list,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._values_resolver = resolver
        self._default_values = default

    def _new_default(self) -> MutableSequenceT:
        new = self._data.new()
        new.extend(self._values_resolver(self._default_values()))
        return new

    @override
    def set(
        self, instance: Any, value: ValueSetT | MutableSequenceT
    ) -> MutableSequenceT:
        data = self.get(instance)
        data.clear()
        data.extend(self._values_resolver(value))
        return data


class KeyedCollectionProperty[
    MutableKeyedCollectionT: MutableKeyedCollection,
    ValueSetT,
](Property[MutableKeyedCollectionT, Iterable[ValueSetT]]):
    """
    A property that contains an :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    _data: KeyedCollectionDefinition[MutableKeyedCollectionT]

    def __init__(
        self,
        data: KeyedCollectionDefinition[MutableKeyedCollectionT],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableKeyedCollectionT], bool] | None = None,
        resolver: Callable[
            [ValueSetT | Iterable[ValueSetT]], Iterable[ValueSetT]
        ] = passthrough,
        default: Callable[[], ValueSetT | Iterable[ValueSetT]] = list,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._values_resolver = resolver
        self._default_values = default

    def _new_default(self) -> MutableKeyedCollectionT:
        new = self._data.new()
        new.add(*self._values_resolver(self._default_values()))
        return new

    @override
    def set(
        self, instance: Any, value: Iterable[ValueSetT] | MutableKeyedCollectionT
    ) -> MutableKeyedCollectionT:
        data = self.get(instance)
        data.clear()
        data.add(*self._values_resolver(value))
        return data
