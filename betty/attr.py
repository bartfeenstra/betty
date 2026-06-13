"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Never

from betty.data import DataDefinition
from betty.prop import HasProps, Prop

if TYPE_CHECKING:
    from betty.datas.aggregate.record import FieldDefinition


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
        field: FieldDefinition[OwnerT, GetT, DataDefinitionT],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.field: Final[FieldDefinition[OwnerT, GetT, DataDefinitionT]] = field
        """
        The attribute's field definition.
        """

    def eq(self, owner: OwnerT, other: GetT | SetT, /) -> bool:
        """
        Compare the owner's attribute value to the other value.
        """
        return self.get(owner) == other
