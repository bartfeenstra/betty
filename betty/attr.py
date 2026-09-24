"""
Object attributes.
"""

from __future__ import annotations

from typing import Any, Final, Never

from betty.data import DataDefinition
from betty.datas.aggregate.record import (
    FieldDefinition,
    ResolvableFieldDefinition,
    resolve_field_definition,
)
from betty.prop import HasProps, Prop


class Attr[
    OwnerT: HasProps,
    GetT,
    SetT: Any = Never,
    DefinitionT: DataDefinition = DataDefinition,
](Prop[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(
        self,
        field: ResolvableFieldDefinition[OwnerT, GetT, DefinitionT],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.field: Final[FieldDefinition[OwnerT, GetT, DefinitionT]] = (
            resolve_field_definition(field)
        )
        """
        The attribute's field definition.
        """

    def normalize(self, owner: OwnerT, value: SetT, /) -> GetT:
        """
        Normalize a value from ``SetT`` to ``GetT``.
        """
        return value
