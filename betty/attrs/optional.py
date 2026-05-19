"""
Optional attributes.
"""

from __future__ import annotations

from typing import final, override

from betty.attr import ProxyAttr
from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.optional import OptionalDefinition
from betty.property import HasProperties


@final
class Optional[OwnerT: HasProperties, GetT, SetT](
    ProxyAttr[OwnerT, GetT | None, SetT | None],
    OwnerAttr[OwnerT, GetT | None, SetT | None],
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: OwnerAttr[OwnerT, GetT, SetT], /):
        super().__init__(
            proxied,
            field=FieldDefinition(
                OptionalDefinition(proxied.field.data),
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
        )
        self._proxied = proxied

    def _omit_dump(self, data: GetT | None) -> bool:
        if data is None:
            return True
        return self._proxied.field.omit_dump(data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        if not self._has_owner_attr(owner):
            self._set_owner_attr(owner, None)

    @override
    def get(self, owner: OwnerT, /) -> GetT | None:
        if self._get_owner_attr(owner) is None:
            return None
        return super().get(owner)

    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> None:
        if value is None:
            self._set_owner_attr(owner, None)
        else:
            super().set(owner, value)
