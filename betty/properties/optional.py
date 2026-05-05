"""
Optional properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.data import DataDefinition
from betty.datas.optional import OptionalDefinition
from betty.portable import PortableData
from betty.property import Property, PropertyNotInitialized

if TYPE_CHECKING:
    from betty.typing import Intersection


@final
class Optional[RequiredDataDefinitionT: DataDefinition, ValueGetT, ValueSetT](
    Property[
        OptionalDefinition[RequiredDataDefinitionT, ValueGetT | None, PortableData],
        ValueGetT | None,
        ValueSetT | None,
    ]
):
    """
    Make another property optional, e.g. allow ``None``.
    """

    def __init__(
        self,
        wrapped: Property[
            Intersection[
                RequiredDataDefinitionT, DataDefinition[ValueGetT, PortableData]
            ],
            ValueGetT,
            ValueSetT,
        ],
        /,
    ):
        def _omit_dump(data: ValueGetT | None) -> bool:
            if data is None:
                return True
            if wrapped.attr.omit_dump is None:
                return False
            return wrapped.attr.omit_dump(data)

        super().__init__(
            OptionalDefinition(wrapped.attr.data),
            label=wrapped.attr.label,
            description=wrapped.attr.description,
            omit_load=wrapped.attr.omit_load,
            omit_dump=_omit_dump,
        )
        self._wrapped = wrapped

    def __set_name__(self, owner: type[Any], name: str) -> None:
        super().__set_name__(owner, name)
        self._wrapped.__set_name__(owner, name)

    @override
    def get(self, instance: Any, /) -> ValueGetT | None:
        try:
            return self._wrapped.get(instance)
        except PropertyNotInitialized:
            return self.set(instance, None)

    @override
    def set(self, instance: Any, value: ValueSetT | None, /) -> ValueGetT:
        if value is None:
            return super().set(instance, value)
        return self._wrapped.set(instance, value)

    def __delete__(self, instance: Any) -> None:
        self.delete(instance)

    def delete(self, instance: Any, /) -> None:
        """
        Delete the value from the instance.
        """
        self.set(instance, None)
