"""
Optional attributes.
"""

from __future__ import annotations

from typing import final, override

from betty.attr import Attr, ProxyAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.optional import OptionalDefinition
from betty.property import HasProperties


@final
class Optional[OwnerT: HasProperties, GetT, SetT](
    ProxyAttr[OwnerT, GetT | None, SetT | None]
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, required_attr: Attr[OwnerT, GetT, SetT], /):
        def _omit_dump(data: GetT | None) -> bool:
            if data is None:
                return True
            if required_attr.attr.omit_dump is None:
                return False
            return required_attr.attr.omit_dump(data)

        super().__init__(
            required_attr,
            attr=AttrDefinition(
                OptionalDefinition(required_attr.attr.data),
                label=required_attr.attr.label,
                description=required_attr.attr.description,
                omit_load=required_attr.attr.omit_load,
                omit_dump=_omit_dump,
            ),
        )

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
