"""
Porters for records using their fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.record import Field, assert_record
from betty.portable import PortableData, PortableMapping, Porter

if TYPE_CHECKING:
    from betty.datas.aggregate.record import RecordDefinition


@final
class FieldsPorter[DataT](Porter[DataT, PortableMapping[PortableData]]):
    """
    Load and dump a record using its fields.
    """

    def __init__(self, record: RecordDefinition[DataT, Porter, Any], /):
        self._record = record
        self._load = assert_record(*[
            Field(selector.element, field.data.porter.load, optional=field.omit_load)
            for selector, field in self._record.fields.items()
        ])

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._record.factory(**self._load(data))

    @override
    def dump(self, data: DataT, /) -> PortableMapping[PortableData]:
        portable = {}
        for selector, field in self._record.fields.items():
            field_data = selector.get(data)
            if not field.omit_dump(data, field_data):
                portable[selector.element] = field.data.porter.dump(field_data)
        return portable
