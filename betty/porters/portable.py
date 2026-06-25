"""
Porters for :py:class:`betty.portable.Portable` types.
"""

from __future__ import annotations

from typing import override

from betty.portable import Portable, PortableData, Porter


class PortablePorter[PortableT: Portable, PortableDataT: PortableData = PortableData](
    Porter[PortableT, PortableDataT]
):
    """
    Expose a portable data type as a porter.
    """

    def __init__(self, cls: type[PortableT]):
        self._cls = cls

    @override
    def load(self, portable: PortableData) -> PortableT:
        return self._cls.load(portable)

    @override
    def dump(self, data: PortableT) -> PortableDataT:
        return data.dump()
