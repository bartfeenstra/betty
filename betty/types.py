import builtins
import sys
from typing import Final

from betty.collections.mapping.dict import FrozenDict

identifiable_immutable_sequence_types: Final[tuple[type, ...]] = (tuple,)
identifiable_mutable_sequence_types: Final[tuple[type, ...]] = (list,)
identifiable_sequence_types: Final[tuple[type, ...]] = (
    *identifiable_immutable_sequence_types,
    *identifiable_mutable_sequence_types,
)
type ImmutableIdentifiableSequence[ValueT] = tuple[ValueT, ...]
type MutableIdentifiableSequence[ValueT] = list[ValueT]
type IdentifiableSequence[ValueT] = (
    ImmutableIdentifiableSequence[ValueT] | MutableIdentifiableSequence[ValueT]
)

_identifiable_immutable_mapping_types = (FrozenDict,)
if sys.version_info >= (3, 15):
    _identifiable_immutable_mapping_types = (
        *_identifiable_immutable_mapping_types,
        builtins.frozendict,
    )
identifiable_immutable_mapping_types: Final[tuple[type, ...]] = (
    _identifiable_immutable_mapping_types
)
identifiable_mutable_mapping_types: Final[tuple[type, ...]] = (dict,)
identifiable_mapping_types: Final[tuple[type, ...]] = (
    *_identifiable_immutable_mapping_types,
    *identifiable_mutable_mapping_types,
)


if sys.version_info >= (3, 15):
    type ImmutableIdentifiableMapping[KeyT, ValueT] = builtins.frozendict[KeyT, ValueT]
else:
    type ImmutableIdentifiableMapping[KeyT, ValueT] = builtins.frozendict[KeyT, ValueT]
type MutableIdentifiableMapping[KeyT, ValueT] = dict[KeyT, ValueT]
if sys.version_info >= (3, 15):
    type IdentifiableMapping[ValueT] = (
        ImmutableIdentifiableMapping[ValueT] | MutableIdentifiableMapping[ValueT]
    )
else:
    # @todo How to support immutable mappings on Python 3.14 and lower?
    type IdentifiableMapping[ValueT] = MutableIdentifiableMapping[ValueT]
