"""
Porters for optional data.
"""

from __future__ import annotations

from typing import final, override

from betty.portable import PortableData, Porter


@final
class OptionalPorter[DataT, PortableDataT: PortableData = PortableData](
    Porter[DataT | None, PortableDataT | None]
):
    """
    Add optional (``None``) support to another porter.
    """

    def __init__(self, proxied: Porter[DataT, PortableDataT]):
        self._proxied = proxied

    @override
    def load(self, data: PortableData) -> DataT | None:
        if data is None:
            return None
        return self._proxied.load(data)

    @override
    def dump(self, data: DataT | None) -> PortableDataT | None:
        if data is None:
            return None
        return self._proxied.dump(data)
