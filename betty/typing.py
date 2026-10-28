"""
Providing typing utilities.
"""

from __future__ import annotations

import builtins
import sys
from typing import Any, Final, TypeIs, final

from betty.collections.mapping.dict import FrozenDict


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
type _CommonRuntimeCheckableImmutableMapping[KeyT, ValueT] = FrozenDict[
    KeyT, ValueT, ValueT
]
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
