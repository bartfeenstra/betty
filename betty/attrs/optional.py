"""
Optional attributes.
"""

from __future__ import annotations

from typing import final, override

from betty.attrs.settable import SettableAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.optional import OptionalDefinition
from betty.prop import HasProps, ProxyProp


@final
class Optional[OwnerT: HasProps, GetT, SetT](
    ProxyProp[OwnerT, GetT | None, SetT | None],
    SettableAttr[OwnerT, GetT | None, SetT | None],
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: SettableAttr[OwnerT, GetT, SetT], /):
        super().__init__(
            FieldDefinition(
                OptionalDefinition(proxied.field.data),
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
            proxied=proxied,
        )
        self._proxied_omit_dump = proxied.field.omit_dump

    def _omit_dump(self, owner: OwnerT, data: GetT | None) -> bool:
        if data is None:
            return True
        return self._proxied_omit_dump(owner, data)

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

    @override
    def get(self, owner: OwnerT, /) -> GetT | None:
        if getattr(owner, self.prop.owner_attr):
            return None
        return super().get(owner)

    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> None:
        if value is None:
            setattr(owner, self.prop.owner_attr, True)
            super().delete_owner(owner)
        else:
            setattr(owner, self.prop.owner_attr, False)
            super().set(owner, value)

    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.set(owner, None)
