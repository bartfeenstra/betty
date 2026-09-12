"""
Porters to conditionally port field data.
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import signature
from typing import TYPE_CHECKING, Any, final, override

from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition, FieldPorter
from betty.portable import NoPortableData

if TYPE_CHECKING:
    from betty.portable import OptionalPortableData, PortableData

type _InternalOmitDump[OwnerT, DataT] = Callable[
    [OwnerT, FieldDefinition[OwnerT, DataT, DataDefinition[DataT]], DataT], bool
]
type _OmitDump[OwnerT, DataT] = (
    _InternalOmitDump[OwnerT, DataT] | Callable[[DataT], bool]
)


@final
class OmitFieldPorter[OwnerT, DataT](FieldPorter[OwnerT, DataT, DataT]):
    """
    Conditionally port field data.
    """

    def __init__(
        self,
        field: FieldDefinition[OwnerT, DataT, DataDefinition],
        omit_dump: _OmitDump[OwnerT, DataT],
        /,
    ):
        self._field = field
        self._omit_dump: _InternalOmitDump[OwnerT, DataT] = (
            omit_dump
            if len(signature(omit_dump).parameters) == 3
            else lambda _, __, data: omit_dump(
                data,  # ty: ignore[invalid-argument-type]
            )  # ty: ignore[invalid-assignment, missing-argument]
        )

    @classmethod
    def new[NewDataT](
        cls, omit_dump: _OmitDump[OwnerT, NewDataT], /
    ) -> Callable[[Any], OmitFieldPorter[OwnerT, NewDataT]]:
        """
        Create a new field porter.
        """
        return lambda field: OmitFieldPorter[OwnerT, DataT](field, omit_dump)

    @override
    def dump(self, owner: OwnerT, data: DataT, /) -> OptionalPortableData:
        if self._omit_dump(owner, self._field, data):
            return NoPortableData
        return self._field.data.porter.dump(data)

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._field.data.porter.load(data)
