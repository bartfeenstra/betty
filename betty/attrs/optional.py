"""
Optional attributes.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import final, override

from betty.attr import Attr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.optional import OptionalDefinition
from betty.porters.omit_field import OmitFieldPorter
from betty.prop import HasProps


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

    @override
    def _pre_init_owner(self, owner: OwnerT, /) -> None:
        self.prop.setattr(owner, None)

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetT | None:
        if self.prop.getattr(owner) is None:
            return None
        return super().get(owner)

    @final
    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> None:
        self.assert_settable(owner)
        if value is None:
            super().delete_owner(owner)
            self.prop.setattr(owner, None)
        else:
            super().set(owner, value)

    @final
    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.assert_deletable(owner)
        self.set(owner, None)


class OptionableAttr[OwnerT: HasProps, GetT, SetT, DataDefinitionT: DataDefinition](
    Attr[OwnerT, GetT, SetT, DataDefinitionT]
):
    """
    An attribute that can be made optional.
    """

    @property
    @abstractmethod
    def optional(self) -> OptionalAttr[OwnerT, GetT | None, SetT | None]:
        """
        Return a new attribute like this one, but that also allows ``None``.
        """
