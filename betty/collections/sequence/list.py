"""
Lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.collections.sequence.adapter import MutableResolvedSequenceAdapter

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.collections import ValueResolver


class List[ValueT, ResolvableValueT](
    MutableResolvedSequenceAdapter[ValueT, ResolvableValueT]
):
    """
    A resolved list.
    """

    def __init__(
        self,
        values: Iterable[ValueT | ResolvableValueT] | None = None,
        /,
        *,
        value_resolver: ValueResolver[ValueT, ResolvableValueT],
    ):
        super().__init__(
            [] if values is None else list(map(value_resolver, values)),
            value_resolver=value_resolver,
        )
