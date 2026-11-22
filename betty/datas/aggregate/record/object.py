"""
Object data types.
"""

from __future__ import annotations

from typing import override

from betty.attr import HasAttrs
from betty.data import Data
from betty.datas.aggregate.record import RecordDefinition
from betty.operator import Attr as AttrOperator


class ObjectDefinition[DataT](RecordDefinition[DataT, AttrOperator]):
    """
    Define an object with attributes.

    Use :py:class:`betty.attr.Attr` to define fields inline, or in superclasses so they can be inherited.
    """

    @override
    def _set_cls(self, cls: type[DataT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, HasAttrs):
            for attr in cls.attrs:
                self._fields[AttrOperator(attr.ownership.name)] = attr.field


class Object[DefinitionT: ObjectDefinition = ObjectDefinition](
    Data[DefinitionT], HasAttrs
):
    """
    An object with attributes.

    This is a mixin, and as such should not be used for type checking.
    """
