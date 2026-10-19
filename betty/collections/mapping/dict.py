"""
Dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections.mapping.adapter import MutableResolvedMappingAdapter
from betty.frosties.attr import AttrFreezable
from betty.functools import passthrough

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


@final
class Dict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    AttrFreezable,
    MutableResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A dictionary.
    """

    def __init__(
        self,
        values: Mapping[ResolvableKeyT, ResolvableValueT] | None = None,
        /,
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT] = passthrough,
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
