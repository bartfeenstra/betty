"""
Field porters wrapping regular porters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.datas.aggregate.record import FieldPorter

if TYPE_CHECKING:
    from betty.nothing import NothingType
    from betty.portable import PortableData, Porter


@final
class PorterFieldPorter[OwnerT, DataT](FieldPorter[OwnerT, DataT, DataT]):
    """
    Port a field using a regular porter.
    """

    def __init__(self, porter: Porter[DataT], /):
        self._porter = porter

    @override
    def dump(self, owner: OwnerT, data: DataT, /) -> PortableData | NothingType:
        return self._porter.dump(data)

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._porter.load(data)
