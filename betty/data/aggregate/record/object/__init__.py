"""
Object data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from inspect import getmembers
from types import FunctionType
from typing import TYPE_CHECKING, Any, Generic, final

from typing_extensions import TypeVar, override

from betty.data import DataDefinition
from betty.data.aggregate.record import FieldDefinition, RecordDefinition
from betty.data.indicator.selector import Attr as AttrElement
from betty.data.indicator.selector import Element
from betty.importlib import fully_qualified_name
from betty.locale.localizable.resolve import resolve_localizable

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

    from betty.data import Data
    from betty.locale.localizable import Localizable, ResolvableLocalizable

_FunctionTypeT = TypeVar("_FunctionTypeT", bound=FunctionType)
_DataClsT = TypeVar("_DataClsT")
_ElementCoT = TypeVar("_ElementCoT", bound=Element[Any], covariant=True)


_attrs: MutableMapping[str, MutableMapping[str, AttrDefinition]] = defaultdict(dict)


@final
class AttrDefinition(Generic[_DataClsT]):
    """
    Define an object attribute.

    Usage:

    .. code-block:: python

       @ObjectDefinition(label="My first object")
       class MyFirstObject(Data[ObjectDefinition]):
           @property
           @AttrDefinition(BoolDefinition(label="My first attribute"))
           def my_first_attr(self) -> bool:
               return True
    """

    def __init__(
        self,
        data: DataDefinition[_DataClsT] | type[Data[DataDefinition[_DataClsT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_DataClsT], bool] | None = None,
    ):
        self._data = data if isinstance(data, DataDefinition) else data.data()
        self._label = None if label is None else resolve_localizable(label)
        self._description = (
            None if description is None else resolve_localizable(description)
        )
        self._omit_load = omit_load
        self._omit_dump = omit_dump

    def field(self, name: str, /) -> FieldDefinition:
        """
        Create a field definition for this attribute.
        """
        return FieldDefinition(
            AttrElement(name),
            self._data,
            label=self._label,
            description=self._description,
            omit_load=self._omit_load,
            omit_dump=self._omit_dump,
        )

    def __call__(self, attribute: _FunctionTypeT) -> _FunctionTypeT:
        """
        Decorate an attribute.
        """
        global _attrs
        cls_name, attribute_name = (
            f"{attribute.__globals__['__spec__'].name}:{attribute.__qualname__}".rsplit(
                ".", 1
            )
        )
        _attrs[cls_name][attribute_name] = self
        return attribute

    @property
    def data(self) -> DataDefinition[_DataClsT]:
        """
        The attribute's data definition.
        """
        return self._data

    @property
    def label(self) -> Localizable | None:
        """
        The human-readable attribute label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long attribute description.
        """
        return self._description

    @property
    def omit_load(self) -> bool | None:
        """
        Check if the field may be omitted from the parent when loading from portable data.
        """
        return self._omit_load

    @property
    def omit_dump(self) -> Callable[[_DataClsT], bool] | None:
        """
        Check if the field may be omitted from the parent when dumping to portable data.
        """
        return self._omit_dump


class Attr(ABC, Generic[_DataClsT]):
    """
    A class attribute that exposes its data definition.
    """

    @property
    @abstractmethod
    def attr(self) -> AttrDefinition[_DataClsT]:
        """
        The attribute's data definition.
        """


class ObjectDefinition(RecordDefinition[_DataClsT, AttrElement]):
    """
    Define an object with attributes.

    Use :py:class:`betty.data.aggregate.record.object.AttrDefinition` to define fields inline, or in superclasses so they
    can be inherited.
    """

    @override
    def _set_cls(self, cls: type[_DataClsT]) -> None:
        global _attrs
        super()._set_cls(cls)
        cls_name = fully_qualified_name(cls)
        attrs = _attrs[cls_name]

        for member_name, member in getmembers(cls):
            if isinstance(member, Attr):
                self._fields.append(member.attr.field(member_name))
            elif member_name in attrs:
                self._fields.append(
                    attrs[member_name].field(member_name),  # ty:ignore[invalid-argument-type]
                )
        return cls  # ty:ignore[invalid-return-type]
