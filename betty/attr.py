"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.functools import passthrough
from betty.property import HasProperties, SettableProperty

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record.object import AttrDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](SettableProperty[OwnerT, GetT, SetT]):
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
class AttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.attr.Attr`.
    """
