"""
Object attributes.
"""

from __future__ import annotations

from typing import Any, Final, Never

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps, Prop


class Attr[
    OwnerT: HasProps,
    GetT,
    SetT: Any = Never,
    DataDefinitionT: DataDefinition = DataDefinition,
](Prop[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(
        self,
        field: FieldDefinition[OwnerT, GetT, DataDefinitionT]
        | ResolvableDataDefinition[DataDefinitionT],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.field: Final[FieldDefinition[OwnerT, GetT, DataDefinitionT]] = (
            field
            if isinstance(field, FieldDefinition)
            else FieldDefinition(resolve_data_definition(field))
        )
        """
        The attribute's field definition.
        """

    def normalize(self, owner: OwnerT, value: SetT, /) -> GetT:
        """
        Normalize a value from ``SetT`` to ``GetT``.
        """
        return value
