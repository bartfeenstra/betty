"""
Porters for :py:class:`betty.datas.aggregate.record.PortableRecord` types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.datas.aggregate.record import PortableRecord, RecordPorter
from betty.indicator.selector import Element
from betty.porters.portable import PortablePorter

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
class PortableRecordPorter[
    PortableRecordT: PortableRecord,
    ElementT: Element[str] = Element[str],
](PortablePorter[PortableRecordT], RecordPorter[PortableRecordT, ElementT]):
    """
    Expose a portable record data type as a porter.
    """

    @override
    def load_key(
        self, portable: PortableData, key: ElementT, portable_key: str, /
    ) -> PortableRecordT:
        return self._cls.load_key(portable, key, portable_key)

    @override
    def dump_key(
        self, data: PortableRecordT, key: ElementT, /
    ) -> tuple[str, PortableData]:
        return data.dump_key(key)
