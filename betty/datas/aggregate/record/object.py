"""
Object data types.
"""

from __future__ import annotations

from typing import Any, override

from betty.attr import Attr
from betty.classtools.class_var import ClassVars
from betty.classtools.init import Init
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
        if issubclass(cls, Object):
            for attr in cls.attrs:
                self._fields[AttrOperator(attr.ownership.name)] = attr.field


class Object[DefinitionT: ObjectDefinition = ObjectDefinition](Data[DefinitionT], Init):
    """
    An object with attributes.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.attrs = ClassVars(cls, Attr)
