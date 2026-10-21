"""
Dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections.mapping.adapter import MutableResolvedMappingAdapter
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.collections import KeyResolver, ValueResolver


@final
class Dict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A resolved dictionary.
    """

    def __init__(
        self,
        values: Mapping[KeyT | ResolvableKeyT, ValueT | ResolvableValueT] | None = None,
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value_resolver: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(
            {}
            if values is None
            else {
                key_resolver(key): value_resolver(value)
                for key, value in values.items()
            },
            key_resolver=key_resolver,
            value_resolver=value_resolver,
        )
