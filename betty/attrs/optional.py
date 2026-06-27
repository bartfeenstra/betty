"""
Optional attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.optional import OptionalDefinition

if TYPE_CHECKING:
    from betty.attr import Attr, Object


class OptionalAttr[OwnerT: Object, GetT, SetT](
    ProxyAttr[OwnerT, GetT | None, SetT | None, DataDefinition[GetT | None]]
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: Attr[OwnerT, GetT, SetT, DataDefinition[GetT]], /):
        super().__init__(
            FieldDefinition(
                OptionalDefinition(proxied.field.data),
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self.__omit_dump,
            ),
            proxied=proxied,
        )

    def __omit_dump(self, owner: OwnerT, data: GetT | None) -> bool:
        if data is None:
            return True
        return self._proxied_field.omit_dump(owner, data)

    @final
    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        try:
            super().get(owner)
        except AttributeError:
            optional = True
        else:
            optional = False
        setattr(owner, self.prop.owner_attr, optional)

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetT | None:
        if getattr(owner, self.prop.owner_attr):
            return None
        return super().get(owner)

    @final
    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> None:
        if value is None:
            setattr(owner, self.prop.owner_attr, True)
            super().delete_owner(owner)
        else:
            setattr(owner, self.prop.owner_attr, False)
            super().set(owner, value)

    @final
    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.set(owner, None)
