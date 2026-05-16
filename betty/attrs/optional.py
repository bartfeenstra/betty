"""
Optional attributes.
"""

from __future__ import annotations

from typing import final, override

from betty.attr import Attr, AttrNotInitialized
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.optional import OptionalDefinition
from betty.property import DeletableProperty, HasProperties


@final
class Optional[OwnerT: HasProperties, GetT, SetT](
    Attr[OwnerT, GetT | None, SetT | None], DeletableProperty[OwnerT, GetT | None]
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
            AttrDefinition(
                OptionalDefinition(required_attr.attr.data),
                label=required_attr.attr.label,
                description=required_attr.attr.description,
                omit_load=required_attr.attr.omit_load,
                omit_dump=_omit_dump,
            )
        )
        self._required_attr = required_attr

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        super().__set_name__(owner, name)
        self._required_attr.__set_name__(owner, name)

    @override
    def get(self, owner: OwnerT, /) -> GetT | None:
        try:
            return self._required_attr.get(owner)
        except AttrNotInitialized:
            return self.set(owner, None)

    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> None:
        if value is None:
            super().set(owner, value)
        else:
            self._required_attr.set(owner, value)

    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.set(owner, None)
