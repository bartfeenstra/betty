"""
Optional attributes.
"""

from __future__ import annotations

from typing import final, override

from betty.attr import Attr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.optional import OptionalDefinition
from betty.property import HasProperties


@final
class Optional[OwnerT: HasProperties, GetT, SetT](
    Attr[OwnerT, GetT | None, SetT | None]
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
    def init_property_owner(self, owner: OwnerT, /) -> None:
        super().init_property_owner(owner)
        setattr(owner, f"_{self.property.name}", None)
        self._required_attr.init_property_owner(owner)

    # @todo I don't think we can fix this at all without DefaultProperty...
    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return getattr(owner, f"_{self.property.name}")

    @override
    def set(self, owner: OwnerT, value: SetT | None, /) -> GetT | None:
        if value is None:
            setattr(owner, f"_{self.property.name}", None)
            return None
        return self._required_attr.set(owner, value)

    def __delete__(self, instance: OwnerT) -> None:
        self.delete(instance)

    def delete(self, owner: OwnerT, /) -> None:
        """
        Delete the value from the instance.
        """
        self.set(owner, None)
