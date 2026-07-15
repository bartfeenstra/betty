"""
Proxy porters.
"""

from __future__ import annotations

from typing import override

from betty.portable import PortableData, Porter


class ProxyPorter[DataT, PortableDataT: PortableData = PortableData](
    Porter[DataT, PortableDataT]
):
    """
    Proxy another porter.
    """

    def __init__(self, *, proxied: Porter[DataT, PortableDataT]):
        self._proxied = proxied

    @override
    def load(self, data: PortableData) -> DataT:
        return self._proxied.load(data)

    @override
    def dump(self, data: DataT) -> PortableDataT:
        return self._proxied.dump(data)
