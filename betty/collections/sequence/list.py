"""
Lists.
"""

from __future__ import annotations

from collections.abc import Reversible
from typing import TYPE_CHECKING, final, override

from betty.collection import SortableCollection, SortKey
from betty.collections.sequence.adapter import MutableSequenceAdapter
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.collections import ValueResolver


class List[ValueT, ResolvableValueT](
    MutableSequenceAdapter[ValueT, ResolvableValueT, list[ValueT]],
    SortableCollection[ValueT],
    Reversible,
):
    """
    A list.
    """

    def __init__(
        self,
        values: Iterable[ValueT | ResolvableValueT] = (),
        /,
        *,
        value_resolver: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(list(map(value_resolver, values)))
        self.__value_resolver = value_resolver

    @final
    @override
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        return self.__value_resolver(value)

    @override
    def reverse(self) -> None:
        self.__wrapped__.reverse()

    @override
    def sort(
        self, *, key: SortKey[ValueT] | None = None, reverse: bool = False
    ) -> None:
        self.__wrapped__.sort(key=key, reverse=reverse)
