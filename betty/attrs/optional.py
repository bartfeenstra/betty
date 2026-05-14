"""
Optional attributes.
"""

from __future__ import annotations

from typing import Any, final, override

from betty.attr import Attr, AttrNotInitialized
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.optional import OptionalDefinition


@final
class Optional[ValueGetT, ValueSetT](Attr[ValueGetT | None, ValueSetT | None]):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, required_attr: Attr[ValueGetT, ValueSetT], /):
        def _omit_dump(data: ValueGetT | None) -> bool:
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

    def __set_name__(self, owner: type[Any], name: str) -> None:
        super().__set_name__(owner, name)
        self._required_attr.__set_name__(owner, name)

    @override
    def get(self, instance: Any, /) -> ValueGetT | None:
        try:
            return self._required_attr.get(instance)
        except AttrNotInitialized:
            return self.set(instance, None)

    @override
    def set(self, instance: Any, value: ValueSetT | None, /) -> ValueGetT | None:
        if value is None:
            return super().set(instance, value)
        return self._required_attr.set(instance, value)

    def __delete__(self, instance: Any) -> None:
        self.delete(instance)

    def delete(self, instance: Any, /) -> None:
        """
        Delete the value from the instance.
        """
        self.set(instance, None)
