"""
Data definition proxy porters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, final, override

from betty.portable import PortableData, Porter

if TYPE_CHECKING:
    from betty.data import DataDefinition


@final
class DataDefinitionProxyPorter[DataT](Porter[DataT]):
    """
    Proxy a data definition's porter.
    """

    def __init__(self, data: DataDefinition[DataT, Never, Porter[DataT]], /):
        self._data = data

    @override
    def load(self, data: PortableData) -> DataT:
        return self._data.porter.load(data)

    @override
    def dump(self, data: DataT) -> PortableData:
        return self._data.porter.dump(data)
