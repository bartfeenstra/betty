"""
Object properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, cast, final, overload

from typing_extensions import override

from betty.data.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.json.linked_data import LinkedDataDumper
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.json.schema import Schema
    from betty.locale.localizable import LocalizableLike
    from betty.portable import PortableData
    from betty.project import Project


_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")


class Property(Attr, LinkedDataDumper[Any], Generic[_ValueGetT, _ValueSetT]):
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
        empty: Callable[[_ValueGetT], bool] | None = None,
        resolver: Callable[[_ValueSetT | _ValueGetT], _ValueGetT] = passthrough,
    ):
        self._data = data
        self._label = label
        self._description = description
        self._empty = empty
        self._attr = AttrDefinition(
            data, label=label, description=description, empty=empty
        )
        self._resolver = resolver

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"

    @override
    @property
    def attr(self) -> AttrDefinition:
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
            instance_name = fully_qualified_name(type(instance))
            raise PropertyNotInitialized(
                f"{instance_name}.{self._attr_name[1:]} was never initialized. {instance_name}.__init__() MUST set a value."
            )
        return value

    def __set__(self, instance: Any, value: _ValueSetT | _ValueGetT) -> None:
        setattr(instance, self._attr_name, self._resolver(value))


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.data.aggregate.record.object.property.Property`.
    """


@final
class Optional(Attr, LinkedDataDumper, Generic[_ValueGetT, _ValueSetT]):
    """
    A base class for properties with optional values.
    """

    def __init__(self, required_property: Property[_ValueGetT, _ValueSetT], /):
        self._required_property = required_property
        self._attr = AttrDefinition(
            required_property._data,
            label=required_property._label,
            description=required_property._description,
            empty=required_property._empty,
            optional=True,
        )

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._attr_name = f"_{name}"
        self._required_property.__set_name__(owner, name)

    @override
    @property
    def attr(self) -> AttrDefinition:
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

    @override
    async def linked_data_schema(self, project: Project, /) -> Schema | Void:
        # @todo Alter the schema to make it optional
        if isinstance(self._required_property, LinkedDataDumper):
            return await self._required_property.linked_data_schema(project)
        return Void()

    @override
    async def dump_linked_data(
        self, project: Project, target: Any, /
    ) -> PortableData | Void:
        if self.__get__(target, type(target)) is None:
            return Void()
        if isinstance(self._required_property, LinkedDataDumper):
            return await self._required_property.dump_linked_data(project, target)
        return Void()
