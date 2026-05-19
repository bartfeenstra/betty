"""
Object data types.
"""

from __future__ import annotations

from inspect import getmembers
from typing import override

from betty.attr import Attr
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
        for name, member in getmembers(cls):
            if isinstance(member, Attr):
                self._fields[AttrElement(name)] = member.field
