"""
Proxy porters.
"""

from __future__ import annotations

from typing import override

from betty.portable import PortableData, Porter


class ProxyPorter[DataClsT, PortableDataT: PortableData = PortableData](
    Porter[DataClsT, PortableDataT]
):
    """
    Proxy another porter.
    """

    def __init__(self, *, proxied: Porter[DataClsT, PortableDataT]):
        self._proxied = proxied

    @override
    def load(self, data: PortableData) -> DataClsT:
        return self._proxied.load(data)

    @override
    def dump(self, data: DataClsT) -> PortableDataT:
        return self._proxied.dump(data)
