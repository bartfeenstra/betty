"""
Object properties.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, MutableMapping, MutableSequence
from typing import TYPE_CHECKING, Any, Generic, Self, cast, final, overload

from typing_extensions import TypeVar, override

from betty.collections import (
    KeyedCollection,
    MutablePrimaryKeyCollection,
)
from betty.data import OptionalDefinition
from betty.data.aggregate.collection.mapping import (
    MappingDefinition,
    PrimaryKeyCollectionDefinition,
)
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")
_MutableMappingT = TypeVar("_MutableMappingT", bound=MutableMapping[Any, Any])
_MutableSequenceT = TypeVar("_MutableSequenceT", bound=MutableSequence[Any])
_MappingDefinitionT = TypeVar("_MappingDefinitionT", bound=MappingDefinition)
_SequenceDefinitionT = TypeVar("_SequenceDefinitionT", bound=SequenceDefinition)
_KeyedCollectionDefinitionT = TypeVar(
    "_KeyedCollectionDefinitionT", bound=PrimaryKeyCollectionDefinition
)
_MutablePrimaryKeyCollectionT = TypeVar(
    "_MutablePrimaryKeyCollectionT", bound=MutablePrimaryKeyCollection
)


class _Property(Attr[_ValueGetT], ABC, Generic[_ValueGetT, _ValueSetT]):
    _attr_name: str

    def __init__(
        self,
        attr: AttrDefinition[_ValueGetT],
        *,
        resolver: Callable[[_ValueSetT | _ValueGetT], _ValueGetT] = passthrough,
    ):
        self._attr = attr
        self._resolver = resolver

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
        return self.get(instance)

    def __set__(self, instance: Any, value: _ValueSetT | _ValueGetT) -> None:
        self.set(instance, value)

    @abstractmethod
    def get(self, instance: Any) -> _ValueGetT:
        """
        Get the property value from the instance.
        """

    def set(self, instance: Any, value: _ValueSetT | _ValueGetT) -> _ValueGetT:
        """
        Set the value on the instance.
        """
        resolved_value = self._resolver(value)
        setattr(instance, self._attr_name, resolved_value)
        return resolved_value


class Property(_Property[_ValueGetT, _ValueSetT]):
    """
    An object attribute with a definition.
    """

    def __init__(
        self,
        data: DataDefinition[_ValueGetT] | type[Data[DataDefinition[_ValueGetT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_ValueGetT], bool] | None = None,
        resolver: Callable[[_ValueSetT | _ValueGetT], _ValueGetT] = passthrough,
        default: Callable[[], _ValueGetT] | None = None,
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
    def get(self, instance: Any) -> _ValueGetT:
        value = cast(
            _ValueGetT | Void,
            getattr(instance, self._attr_name, Void()),
        )
        if isinstance(value, Void):
            if self._default is None:
                instance_name = fully_qualified_name(type(instance))
                raise PropertyNotInitialized(
                    f"{instance_name}.{self._attr_name[1:]} was never initialized. Either provide a default when initializing the property, or make {instance_name}.__init__() set a value."
                )
            value = self._default()
            setattr(instance, self._attr_name, value)
        return value


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.data.aggregate.record.object.property.Property`.
    """


@final
class Optional(_Property[_ValueGetT | None, _ValueSetT | None]):
    """
    Make another property optional, e.g. allow ``None``.
    """

    def __init__(self, required_property: Property[_ValueGetT, _ValueSetT], /):
        def _omit_dump(data: _ValueGetT | None) -> bool:
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
    def get(self, instance: Any) -> _ValueGetT | None:
        try:
            return self._required_property.get(instance)
        except PropertyNotInitialized:
            return self.set(instance, None)

    @override
    def set(self, instance: Any, value: _ValueSetT | _ValueGetT | None) -> _ValueGetT:
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


class MappingProperty(Property[_MutableMappingT, _ValueSetT]):
    """
    A property that contains a :py:class:`collections.abc.MutableMapping`.
    """

    def __init__(
        self,
        data: Intersection[DataDefinition[_MutableMappingT], _MappingDefinitionT]
        | Data[Intersection[DataDefinition[_MutableMappingT], _MappingDefinitionT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_MutableMappingT], bool] | None = None,
        resolver: Callable[
            [_ValueSetT | _MutableMappingT], _MutableMappingT
        ] = passthrough,
        default: Callable[[], _MutableMappingT] | None = None,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            resolver=resolver,
            default=default,
        )

    @override
    def set(
        self, instance: Any, value: _ValueSetT | _MutableMappingT
    ) -> _MutableMappingT:
        configurations = self.get(instance)
        configurations.clear()
        resolved_value = self._resolver(value)
        configurations.update(resolved_value)
        return resolved_value


class SequenceProperty(Property[_MutableSequenceT, _ValueSetT]):
    """
    A property that contains a :py:class:`collections.abc.MutableSequence`.
    """

    def __init__(
        self,
        data: Intersection[DataDefinition[_MutableSequenceT], _SequenceDefinitionT]
        | Data[Intersection[DataDefinition[_MutableSequenceT], _SequenceDefinitionT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_MutableSequenceT], bool] | None = None,
        resolver: Callable[
            [_ValueSetT | _MutableSequenceT], _MutableSequenceT
        ] = passthrough,
        default: Callable[[], _MutableSequenceT] | None = None,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            resolver=resolver,
            default=default,
        )

    @override
    def set(
        self, instance: Any, value: _ValueSetT | _MutableSequenceT
    ) -> _MutableSequenceT:
        configurations = self.get(instance)
        configurations.clear()
        resolved_value = self._resolver(value)
        configurations.extend(resolved_value)
        return resolved_value


class PrimaryKeyCollectionProperty(
    Property[_MutablePrimaryKeyCollectionT, Iterable[_ValueSetT]]
):
    """
    A property that contains an :py:class:`betty.collections.PrimaryKeyCollection`.
    """

    def __init__(
        self,
        data: PrimaryKeyCollectionDefinition[
            Intersection[
                _MutablePrimaryKeyCollectionT,
                KeyedCollection[Any, Any, Any, _ValueSetT],
            ]
        ],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_MutablePrimaryKeyCollectionT], bool] | None = None,
        resolver: Callable[
            [_ValueSetT | _MutablePrimaryKeyCollectionT], Iterable[_ValueGetT]
        ] = passthrough,
        default: Callable[[], KeyedCollection] | None = None,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            resolver=resolver,
            default=default,
        )

    @override
    def set(
        self, instance: Any, value: Iterable[_ValueSetT] | _MutablePrimaryKeyCollectionT
    ) -> _MutablePrimaryKeyCollectionT:
        collection = self.get(instance)
        collection.clear()
        resolved_value = self._resolver(value)
        for resolved_item_value in resolved_value:
            collection.add(resolved_item_value)
        return resolved_value
