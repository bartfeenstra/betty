"""
Optional attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.optional import OptionalDefinition
from betty.porters.omit_field import OmitFieldPorter
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.attr import Attr


class OptionalAttr[OwnerT: HasProps, GetT, SetT](
    ProxyAttr[OwnerT, GetT | None, SetT | None, DataDefinition[GetT | None]]
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: Attr[OwnerT, GetT, SetT, DataDefinition[GetT]], /):
        super().__init__(
            FieldDefinition[OwnerT, GetT, DataDefinition[GetT | None]](
                OptionalDefinition(proxied.field.data),
                label=proxied.field.label,
                description=proxied.field.description,
                optional=True,
                porter=OmitFieldPorter.new(lambda data: data is None),
            ),
            proxied=proxied,
        )

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
