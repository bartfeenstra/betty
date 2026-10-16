"""
Reusable dictionaries.
"""

from collections.abc import Callable, Mapping
from typing import final

from betty.collections.mapping.adapter import (
    MutableResolvedMappingAdapter,
    ResolvedMappingAdapter,
)
from betty.freezer import Frozen
from betty.functools import passthrough


class _Dict[KeyT, ResolvableKeyT, ValueT](
    ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT]
):
    @final
    def __init__(
        self,
        values: Mapping[KeyT, ValueT],
        /,
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
    ):
        super().__init__(dict(values), key_resolver=key_resolver)


@final
class Dict[KeyT, ResolvableKeyT, ValueT](_Dict[KeyT, ResolvableKeyT, ValueT]):
    """
    A dictionary.
    """


@final
class FrozenDict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _Dict[KeyT, ResolvableKeyT, ValueT],
    MutableResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
    Frozen,
):
    """
    A frozen (immutable) dictionary.
    """
