"""
Porters for records using their fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.record import Field, assert_record
from betty.portable import NoPortableData, PortableData, PortableMapping, Porter

if TYPE_CHECKING:
    from betty.datas.aggregate.record import RecordDefinition


@final
class FieldsPorter[DataT](Porter[DataT, PortableMapping]):
    """
    Load and dump a record using its fields.
    """

    def __init__(self, record: RecordDefinition[DataT, Any], /):
        self._record = record
        self._load = assert_record(*[
            Field(operator.operator, field_porter.load, optional=field.optional)
            for operator, field in self._record.fields.items()
            if (field_porter := field.try_porter)
        ])

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._record.new(**self._load(data))

    @override
    def dump(self, data: DataT, /) -> PortableMapping:
        portable = {}
        for operator, field in self._record.fields.items():
            if field_porter := field.try_porter:
                field_data = operator.get(data)
                if (
                    field_dump := field_porter.dump(data, field_data)
                ) is not NoPortableData:
                    portable[operator.operator] = field_dump
        return portable
