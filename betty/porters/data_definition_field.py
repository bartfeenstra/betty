"""
Field porters wrapping data definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.datas.aggregate.record import FieldPorter

if TYPE_CHECKING:
    from betty.data import DataDefinition
    from betty.nothing import NothingType
    from betty.portable import PortableData


@final
class DataDefinitionFieldPorter[OwnerT, DataT](FieldPorter[OwnerT, DataT, DataT]):
    """
    Port field data using the data definition's porter.
    """

    def __init__(self, data: DataDefinition[DataT], /):
        self._data = data

    @override
    def dump(self, owner: OwnerT, data: DataT, /) -> PortableData | NothingType:
        return self._data.porter.dump(data)

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._data.porter.load(data)
