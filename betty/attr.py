"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.functools import passthrough
from betty.property import HasProperties, Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record.object import AttrDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](Property[OwnerT, GetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(
        self,
        attr: AttrDefinition[GetT],
        *,
        resolver: Callable[[SetT | GetT], GetT] = passthrough,
    ):
        self.attr: Final[AttrDefinition[GetT]] = attr
        """
        The attribute's data definition.
        """
        self._resolver = resolver

    @final
    def __set__(self, instance: OwnerT, value: SetT | GetT) -> None:
        self.set(instance, value)

    def set(self, owner: OwnerT, value: SetT, /) -> GetT:
        """
        Set the value on the owner.
        """
        resolved_value = self._resolver(value)
        setattr(owner, f"_{self.property.name}", resolved_value)
        return resolved_value


@final
class AttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.attr.Attr`.
    """
