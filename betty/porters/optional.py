"""
Porters for optional data.
"""

from __future__ import annotations

from typing import final, override

from betty.portable import PortableData, Porter


@final
class OptionalPorter[DataT](Porter[DataT | None]):
    """
    Add optional (``None``) support to another porter.
    """

    def __init__(self, proxied: Porter[DataT]):
        self._proxied = proxied

    @override
    def load(self, data: PortableData) -> DataT | None:
        if data is None:
            return None
        return self._proxied.load(data)

    @override
    def dump(self, data: DataT | None) -> PortableData:
        if data is None:
            return None
        return self._proxied.dump(data)
