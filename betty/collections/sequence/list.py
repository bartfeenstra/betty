"""
Lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.collection import SortableCollection, SortKey
from betty.collections.sequence.adapter import MutableSequenceAdapter

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.collections import ValueResolver


class List[ValueT, ResolvableValueT](
    MutableSequenceAdapter[ValueT, ResolvableValueT, list[ValueT]],
    SortableCollection[ValueT],
):
    """
    A resolved list.
    """

    def __init__(
        self,
        values: Iterable[ValueT | ResolvableValueT] = (),
        /,
        *,
        value_resolver: ValueResolver[ValueT, ResolvableValueT],
    ):
        super().__init__(
            list(map(value_resolver, values)), value_resolver=value_resolver
        )

    @override
    def sort(
        self, *, key: SortKey[ValueT] | None = None, reverse: bool = False
    ) -> None:
        self.__wrapped__.sort(key=key, reverse=reverse)
