"""
Porters for optional daa.
"""

from __future__ import annotations

from typing import final, override

from betty.portable import PortableData, Porter


@final
class OptionalPorter[PortableT, PortableDataT: PortableData = PortableData](
    Porter[PortableT | None, PortableDataT | None]
):
    """
    Add optional (``None``) support to another porter.
    """

    def __init__(self, proxied: Porter[PortableT, PortableDataT]):
        self._proxied = proxied

    @override
    def load(self, portable: PortableData) -> PortableT | None:
        if portable is None:
            return None
        return self._proxied.load(portable)

    @override
    def dump(self, data: PortableT | None) -> PortableDataT | None:
        if data is None:
            return None
        return self._proxied.dump(data)
