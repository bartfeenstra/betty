"""
Porters for records as mappings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.datas.aggregate.record import RecordPorter
from betty.indicator.selector import Element

if TYPE_CHECKING:
    from betty.datas.aggregate.record import RecordDefinition
    from betty.portable import PortableData, PortableMapping


@final
class RecordMappingPorter[DataClsT, ElementT: Element[str] = Element[str]](
    RecordPorter[DataClsT]
):
    """
    Load and dump a record from and to portable mappings.
    """

    def __init__(self, record: RecordDefinition[DataClsT, ElementT], /):
        self._record = record
        self._load = assert_record(*[
            Field(selector.element, field.data.porter.load, optional=field.omit_load)
            for selector, field in record.fields.items()
        ])
        self._load_keyed = assert_mapping()

    @override
    def load(self, portable: PortableData, /) -> DataClsT:
        return self._record.factory(**self._load(portable))

    @override
    def dump(self, data: DataClsT, /) -> PortableMapping:
        portable = {}
        for selector, field in self._record.fields.items():
            field_data = selector.get(data)
            if not field.omit_dump(data, field_data):
                portable[selector.element] = field.data.porter.dump(field_data)
        return portable

    @override
    def load_key(
        self,
        portable: PortableData,
        key: ElementT,
        portable_key: str,
        /,
    ) -> DataClsT:  # ty:ignore[invalid-method-override]
        return self.load({**self._load_keyed(portable), key.element: portable_key})

    @override
    def dump_key(
        self,
        data: DataClsT,
        key: ElementT,
        /,
    ) -> tuple[str, PortableData]:  # ty:ignore[invalid-method-override]
        portable = self.dump(data)
        portable_key = portable.pop(key.element)
        assert isinstance(portable_key, str)
        return portable_key, portable
