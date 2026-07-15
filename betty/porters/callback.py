"""
Porters using callbacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.portable import PortableData, Porter

if TYPE_CHECKING:
    from collections.abc import Callable


@final
class CallbackPorter[DataT, PortableDataT: PortableData = PortableData](
    Porter[DataT, PortableDataT]
):
    """
    Make data portable using a separate loader and dumper.
    """

    def __init__(
        self,
        loader: Callable[[PortableData], DataT],
        dumper: Callable[[DataT], PortableDataT],
        /,
    ):
        self._loader = loader
        self._dumper = dumper

    @override
    def load(self, data: PortableData) -> DataT:
        return self._loader(data)

    @override
    def dump(self, data: DataT) -> PortableDataT:
        return self._dumper(data)
