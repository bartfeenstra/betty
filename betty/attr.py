"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Never, Self, final

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps, Prop

if TYPE_CHECKING:
    from collections.abc import Iterable


class HasAttrs(HasProps):
    """
    An object that has :py:class:`attributes <betty.attr.Attr>`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for prop in self.props():
            prop.init_owner(self)

    @final
    @classmethod
    def attrs(cls) -> Iterable[Attr[Self, Any]]:
        """
        Get all attributes on this class.
        """
        for prop in cls.props():
            if isinstance(prop, Attr):
                yield prop


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
