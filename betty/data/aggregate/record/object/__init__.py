"""
Object data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from inspect import getmembers
from types import FunctionType
from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.data.aggregate.record import FieldDefinition, RecordDefinition
from betty.data.indicator.selector import Attr as AttrElement
from betty.data.indicator.selector import Element
from betty.importlib import fully_qualified_name

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import LocalizableLike

_FunctionTypeT = TypeVar("_FunctionTypeT", bound=FunctionType)
_DataClsT = TypeVar("_DataClsT")
_ElementT = TypeVar("_ElementT", bound=Element[Any])


_attrs: MutableMapping[str, MutableMapping[str, AttrDefinition]] = defaultdict(dict)


@final
class AttrDefinition:
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
        data: DataDefinition[_DataClsT] | Data[DataDefinition[_DataClsT]],
        *,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
        optional: bool = False,
        empty: Callable[[_DataClsT], bool] | None = None,
    ):
        self._data = data
        self._label = label
        self._description = description
        self._optional = optional
        self._empty = empty

    def field(self, name: str, /) -> FieldDefinition:
        """
        Create a field definition for this attribute.
        """
        return FieldDefinition(
            AttrElement(name),
            self._data,
            label=self._label,
            description=self._description,
            optional=self._optional,
            empty=self._empty,
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


class Attr(ABC):
    """
    A class attribute that exposes its data definition.
    """

    @property
    @abstractmethod
    def attr(self) -> AttrDefinition:
        """
        The attribute's data definition.
        """


@final
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
                self._fields.append(attrs[member_name].field(member_name))
        return cls  # ty:ignore[invalid-return-type]
