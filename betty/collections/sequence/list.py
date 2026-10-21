"""
Lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from typing_extensions import disjoint_base

from betty.collections.sequence.adapter import MutableSequenceAdapter
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.collections import ValueResolver


@disjoint_base
class List[ValueT, ResolvableValueT](
    MutableSequenceAdapter[ValueT, ResolvableValueT, list[ValueT]]
):
    """
    A list.
    """

    __slots__ = ("__value_resolver",)

    def __init__(
        self,
        values: Iterable[ValueT | ResolvableValueT] = (),
        /,
        *,
        value: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(list(map(value, values)))
        self.__value_resolver = value

    @final
    @override
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        return self.__value_resolver(value)
