"""
Proxy porters.
"""

from __future__ import annotations

from typing import override

from betty.portable import PortableData, Porter


class ProxyPorter[DataT](Porter[DataT]):
    """
    Proxy another porter.
    """

    def __init__(self, *, proxied: Porter[DataT]):
        self._proxied = proxied

    @override
    def load(self, data: PortableData) -> DataT:
        return self._proxied.load(data)

    @override
    def dump(self, data: DataT) -> PortableData:
        return self._proxied.dump(data)
