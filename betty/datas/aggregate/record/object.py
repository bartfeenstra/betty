"""
Object data types.
"""

from __future__ import annotations

from typing import override

from betty.attr import Attr
from betty.datas.aggregate.record import RecordDefinition
from betty.indicator.operator import Attr as AttrOperator
from betty.portable import Porter
from betty.prop import HasProps


class ObjectDefinition[DataT, PorterT: Porter = Porter](
    RecordDefinition[DataT, AttrOperator, PorterT]
):
    """
    Define an object with attributes.

    Use :py:class:`betty.attr.Attr` to define fields inline, or in superclasses so they can be inherited.
    """

    @override
    def _set_cls(self, cls: type[DataT], /) -> None:
        if issubclass(cls, HasProps):
            for prop in cls.props():
                if isinstance(prop, Attr):
                    self._fields[AttrOperator(prop.prop.name)] = prop.field  # ty:ignore[invalid-assignment]
        super()._set_cls(cls)
