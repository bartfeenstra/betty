"""
Data definition proxy porters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.portable import PortableData, Porter

if TYPE_CHECKING:
    from betty.data import DataDefinition


@final
class DataDefinitionProxyPorter[DataClsT, PortableDataT: PortableData = PortableData](
    Porter[DataClsT, PortableDataT]
):
    """
    Proxy a data definition's porter.
    """

    def __init__(
        self, data: DataDefinition[DataClsT, Porter[DataClsT, PortableDataT]], /
    ):
        self._data = data

    @override
    def load(self, data: PortableData) -> DataClsT:
        return self._data.porter.load(data)

    @override
    def dump(self, data: DataClsT) -> PortableDataT:
        return self._data.porter.dump(data)
