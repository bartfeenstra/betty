"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Never

from betty.prop import HasProps, Prop

if TYPE_CHECKING:
    from betty.datas.aggregate.record import FieldDefinition


class Attr[OwnerT: HasProps, GetT, SetT: Any = Never](Prop[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(self, field: FieldDefinition[OwnerT, GetT], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.field: Final[FieldDefinition[OwnerT, GetT]] = field
        """
        The attribute's field definition.
        """
