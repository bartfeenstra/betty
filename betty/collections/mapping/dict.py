"""
Dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.collections.mapping.adapter import MutableMappingAdapter
from betty.pipeline import pipe
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.collections import KeyResolver, ValueResolver


class Dict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableMappingAdapter[
        KeyT, ResolvableKeyT, ValueT, ResolvableValueT, dict[KeyT, ValueT]
    ],
):
    """
    A resolved dictionary.
    """

    def __init__(
        self,
        values: Mapping[
            KeyT | ResolvableKeyT, ValueT | ResolvableValueT
        ] = empty_frozen_dict,
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value_resolver: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(
            {key_resolver(key): value_resolver(value) for key, value in values.items()},
            key_resolver=key_resolver,
            value_resolver=value_resolver,
        )
