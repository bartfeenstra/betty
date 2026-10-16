"""
Providing typing utilities.
"""

from __future__ import annotations

import builtins
import sys
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Final, TypeIs, final, overload


@final
class Unreachable(NotImplementedError):
    """
    Raised when a line of code is supposed to be unreachable, but was executed anyway.

    Use ``raise Unreachable`` to satisfy type checkers as well as tell Betty's code coverage collection to ignore that
    line.
    """

    def __init__(self, reason: str | None = None):
        super().__init__(
            f"This code was marked unreachable, and this line should never have been executed{'' if reason is None else f', because {reason}'}."
        )


type _CommonFrozenDict[KeyT, ValueT] = dict[KeyT, ValueT] | FrozenDict[KeyT, ValueT]
if sys.version_info >= (3, 15):
    type _OtherFrozenDict[KeyT, ValueT] = (
        _CommonFrozenDict[KeyT, ValueT] | builtins.frozendict[KeyT, ValueT]
    )
else:
    type _OtherFrozenDict[KeyT, ValueT] = _CommonFrozenDict[KeyT, ValueT]


@final
class FrozenDict[KeyT, ValueT](Mapping[KeyT, ValueT]):
    """
    A frozen (immutable) dictionary.

    This class exists for compatibility with Python 3.14 and lower. Once Betty no longer supports those versions, this
    class will be removed entirely, in favor of Python 3.15's ``frozendict``.
    """

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[KeyT, ValueT] | None = None, /):
        self._values = {} if values is None else dict(values)

    def __getitem__(self, key: KeyT, /) -> ValueT:
        return self._values[key]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[KeyT]:
        return iter(self._values)

    def __hash__(self) -> int:
        return hash(tuple(self._values.items()))

    def __or__[OtherKeyT, OtherValueT](
        self, other: _OtherFrozenDict[OtherKeyT, OtherValueT], /
    ) -> FrozenDict[KeyT | OtherKeyT, ValueT | OtherValueT]:
        return FrozenDict(
            self._values | (other._values if isinstance(other, FrozenDict) else other)
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
        return cls(dict.fromkeys(keys, value))

    def reversed(self) -> Iterator[KeyT]:
        """
        Get an iterator that iterators over the keys in reverse.
        """
        return reversed(self._values)


empty_frozen_dict: Final[FrozenDict[Any, Any]] = FrozenDict()


# The following types, type aliases, and functions work over concrete Python types that are:
# - runtime-checkable
# - disjoint
runtime_checkable_sequence_types: Final[tuple[type, ...]] = (list, tuple)
_common_runtime_checkable_mapping_types = (dict, FrozenDict)
if sys.version_info >= (3, 15):
    runtime_checkable_mapping_types: Final[tuple[type, ...]] = (
        *_common_runtime_checkable_mapping_types,
        builtins.frozendict,
    )
else:
    runtime_checkable_mapping_types: Final[tuple[type, ...]] = (
        _common_runtime_checkable_mapping_types
    )
type RuntimeCheckableImmutableSequence[ValueT] = tuple[ValueT, ...]
type RuntimeCheckableMutableSequence[ValueT] = list[ValueT]
type RuntimeCheckableSequence[ValueT] = (
    RuntimeCheckableImmutableSequence[ValueT] | RuntimeCheckableMutableSequence[ValueT]
)
type _CommonRuntimeCheckableImmutableMapping[KeyT, ValueT] = FrozenDict[KeyT, ValueT]
if sys.version_info >= (3, 15):
    type RuntimeCheckableImmutableMapping[KeyT, ValueT] = (
        _CommonRuntimeCheckableImmutableMapping[KeyT, ValueT]
        | builtins.frozendict[KeyT, ValueT]
    )
else:
    type RuntimeCheckableImmutableMapping[KeyT, ValueT] = (
        _CommonRuntimeCheckableImmutableMapping[KeyT, ValueT]
    )
type RuntimeCheckableMutableMapping[KeyT, ValueT] = dict[KeyT, ValueT]
type RuntimeCheckableMapping[KeyT, ValueT] = (
    RuntimeCheckableImmutableMapping[KeyT, ValueT]
    | RuntimeCheckableMutableMapping[KeyT, ValueT]
)


def is_runtime_checkable_sequence(value: Any, /) -> TypeIs[RuntimeCheckableSequence]:
    """
    Check that a value is a sequence of a type checkable at runtime.
    """
    return isinstance(value, runtime_checkable_sequence_types)


def is_runtime_checkable_mapping(value: Any, /) -> TypeIs[RuntimeCheckableMapping]:
    """
    Check that a value is a mapping of a type checkable at runtime.
    """
    return isinstance(value, runtime_checkable_mapping_types)
