"""
Porters to conditionally port field data.
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import signature
from typing import TYPE_CHECKING, Any, final, override

from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition, FieldPorter
from betty.nothing import Nothing, NothingType

if TYPE_CHECKING:
    from betty.capability import CapabilityManufacturer
    from betty.portable import PortableData

type OmitDump[OwnerT, DataT] = Callable[
    [
        OwnerT,
        FieldDefinition[OwnerT, DataT, DataDefinition[DataT]],
        DataT,
    ],
    bool,
]


@final
class OmitFieldPorter[OwnerT, DataT](FieldPorter[OwnerT, DataT, DataT]):
    """
    Conditionally port field data.
    """

    def __init__(
        self,
        field: FieldDefinition[
            OwnerT,
            DataT,
            DataDefinition,
            FieldPorter[OwnerT, DataT],
        ],
        omit_dump: Callable[[DataT], bool] | OmitDump[OwnerT, DataT],
        /,
    ):
        self._field = field
        self._omit_dump: OmitDump[OwnerT, DataT] = (
            omit_dump
            if len(signature(omit_dump).parameters) == 3
            else lambda _, __, data: omit_dump(data)  # ty:ignore[invalid-assignment, missing-argument]
        )

    @classmethod
    def new[NewDataT](
        cls, omit_dump: Callable[[NewDataT], bool] | OmitDump[OwnerT, NewDataT], /
    ) -> CapabilityManufacturer[Any, OmitFieldPorter[OwnerT, NewDataT]]:
        """
        Create a new capability manufacturer.
        """
        return lambda field: OmitFieldPorter[OwnerT, DataT](field, omit_dump)

    @override
    def dump(self, owner: OwnerT, data: DataT, /) -> PortableData | NothingType:
        if self._omit_dump(owner, self._field, data):
            return Nothing
        return self._field.data.porter.dump(data)

    @override
    def load(self, data: PortableData, /) -> DataT:
        return self._field.data.porter.load(data)
