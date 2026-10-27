"""
Dictionaries.
"""

from __future__ import annotations

import builtins
import sys
from typing import TYPE_CHECKING, Any, Final, final, overload, override

from betty.collections.mapping.adapter import MappingAdapter, MutableMappingAdapter
from betty.freezer import Frozen
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.collections import KeyResolver, ValueResolver


type _CommonFrozenDict[KeyT, ValueT] = (
    dict[KeyT, ValueT] | FrozenDict[KeyT, KeyT, ValueT]
)
if sys.version_info >= (3, 15):
    type _OtherFrozenDict[KeyT, ValueT] = (
        _CommonFrozenDict[KeyT, ValueT] | builtins.frozendict[KeyT, ValueT]
    )
else:
    type _OtherFrozenDict[KeyT, ValueT] = _CommonFrozenDict[KeyT, ValueT]


class _Dict[KeyT, ResolvableKeyT, ValueT](
    MappingAdapter[KeyT, ResolvableKeyT, ValueT, dict[KeyT, ValueT]],
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


class FrozenDict[KeyT, ResolvableKeyT, ValueT](
    _Dict[KeyT, ResolvableKeyT, ValueT], Frozen
):
    """
    A frozen (immutable) dictionary.
    """

    __slots__ = ()

    def __hash__(self) -> int:
        return hash(tuple(self.__wrapped__.items()))

    def __or__[OtherKeyT, OtherValueT](
        self, other: _OtherFrozenDict[OtherKeyT, OtherValueT], /
    ) -> FrozenDict[KeyT | OtherKeyT, ValueT | OtherValueT]:
        # @todo this would benefit from a derive() factory on our own to-be-added BettyCollection?
        return FrozenDict(
            self.__wrapped__
            | (other._values if isinstance(other, FrozenDict) else other)
        )

    def __ior__[OtherKeyT, OtherValueT](
        self, other: _OtherFrozenDict[OtherKeyT, OtherValueT], /
    ) -> FrozenDict[KeyT | OtherKeyT, ValueT | OtherValueT]:
        return self.__or__(other)

    @overload
    @classmethod
    def fromkeys[FromKeyT, FromValueT](
        cls, keys: Iterable[FromKeyT], value: FromValueT, /
    ) -> FrozenDict[FromKeyT, FromValueT]:
        pass

    @overload
    @classmethod
    def fromkeys[FromKeyT](
        cls, keys: Iterable[FromKeyT], value: None = None, /
    ) -> FrozenDict[FromKeyT, None]:
        pass

    @classmethod
    def fromkeys(cls, keys, value=None, /):
        """
        Create a new instance from the given keys and value.
        """
        # @todo this would benefit from a derive() factory on our own to-be-added BettyCollection?
        return cls(dict.fromkeys(keys, value))


empty_frozen_dict: Final[FrozenDict[Any, Any, Any]] = FrozenDict()


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
