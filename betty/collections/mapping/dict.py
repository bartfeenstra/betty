"""
Dictionaries.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final, final, override

from typing_extensions import disjoint_base

from betty.collections.mapping.adapter import MappingAdapter, MutableMappingAdapter
from betty.freezer import Frozen
from betty.pipeline import pipe

if TYPE_CHECKING:
    from betty.collections import KeyResolver, ValueResolver


class _Dict[KeyT, ResolvableKeyT, ValueT](
    MappingAdapter[KeyT, ResolvableKeyT, ValueT, dict[KeyT, ValueT]], Mapping[Any, Any]
):
    __slots__ = ("__key_resolver",)

    def __init__(
        self,
        values: Mapping[KeyT | ResolvableKeyT, ValueT] | None = None,
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
    ):
        super().__init__(
            {}
            if values is None
            else {key(key_): value for key_, value in values.items()}
        )
        self.__key_resolver = key

    @final
    @override
    def resolve_key(self, key: KeyT | ResolvableKeyT, /) -> KeyT:
        return self.__key_resolver(key)


@disjoint_base
class FrozenDict[KeyT, ResolvableKeyT, ValueT](
    _Dict[KeyT, ResolvableKeyT, ValueT], Frozen
):
    """
    A frozen (immutable) dictionary.
    """

    __slots__ = ()

    def __hash__(self) -> int:
        return hash(tuple(self.__wrapped__.items()))


empty_frozen_dict: Final[FrozenDict[Any, Any, Any]] = FrozenDict()


@disjoint_base
class Dict[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _Dict[KeyT, ResolvableKeyT, ValueT],
    MutableMappingAdapter[
        KeyT, ResolvableKeyT, ValueT, ResolvableValueT, dict[KeyT, ValueT]
    ],
):
    """
    A dictionary.
    """

    __slots__ = ("__value_resolver",)

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
        super().__init__(
            {key: value(value_) for key, value_ in values.items()}, key=key
        )
        self.__value_resolver = value

    @final
    @override
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        return self.__value_resolver(value)
