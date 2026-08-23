"""
Lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections.sequence.adapter import MutableResolvedSequenceAdapter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


@final
class ResolvedList[ValueT, ResolvableValueT](
    MutableResolvedSequenceAdapter[ValueT, ResolvableValueT]
):
    """
    Resolve values before storing them in a list.
    """

    def __init__(
        self,
        values: Iterable[ValueT] | None = None,
        *,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT],
    ):
        super().__init__(
            [] if values is None else list(map(value_resolver, values)),
            value_resolver=value_resolver,
        )
