"""
Dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.collections.mapping.adapter import MutableMappingAdapter
from betty.pipeline import pipe
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.collections import KeyResolver, ValueResolver


# @todo Move FrozenDict here too


class Dict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableMappingAdapter[
        KeyT, ResolvableKeyT, ValueT, ResolvableValueT, dict[KeyT, ValueT]
    ],
):
    """
    A dictionary.
    """

    __slots__ = ("__key_resolver", "__value_resolver")

    def __init__(
        self,
        values: Mapping[
            KeyT | ResolvableKeyT, ValueT | ResolvableValueT
        ] = empty_frozen_dict,
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__({key(key): value(value) for key, value in values.items()})
        self.__key_resolver = key
        self.__value_resolver = value

    @final
    @override
    def resolve_key(self, key: KeyT | ResolvableKeyT, /) -> KeyT:
        return self.__key_resolver(key)

    @final
    @override
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        return self.__value_resolver(value)
