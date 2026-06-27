"""
Object data types.
"""

from __future__ import annotations

from typing import override

from betty.attr import Attr, Object
from betty.datas.aggregate.record import RecordDefinition
from betty.indicator.selector import Attr as AttrElement


class ObjectDefinition[DataClsT](RecordDefinition[DataClsT, AttrElement]):
    """
    Define an object with attributes.

    Use :py:class:`betty.attr.Attr` to define fields inline, or in superclasses so they can be inherited.
    """

    @override
    def _set_cls(self, cls: type[DataClsT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Object):
            for attr in cls.attrs():
                if isinstance(attr, Attr):
                    self._fields[AttrElement(attr.prop.name)] = attr.field
