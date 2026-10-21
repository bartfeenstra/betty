"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Final, TypeGuard

from typing_extensions import sentinel

from betty.collections.mapping.dict import FrozenDict
from betty.typing import (
    RuntimeCheckableImmutableMapping,
    RuntimeCheckableImmutableSequence,
    RuntimeCheckableMutableMapping,
    RuntimeCheckableMutableSequence,
    Unreachable,
    is_runtime_checkable_mapping,
    is_runtime_checkable_sequence,
)

NoPortableData = sentinel("NoPortableData")

_portable_scalar_types: Final[tuple[type, ...]] = (bool, int, float, str)
type PortableScalar = None | bool | int | float | str
type ImmutablePortableSequence[
    ValueT: ImmutablePortableData = ImmutablePortableData
] = RuntimeCheckableImmutableSequence[ValueT]
type MutablePortableSequence[ValueT: MutablePortableData = MutablePortableData] = (
    RuntimeCheckableMutableSequence[ValueT]
)
type PortableSequence = ImmutablePortableSequence | MutablePortableSequence
type ImmutablePortableMapping[ValueT: ImmutablePortableData = ImmutablePortableData] = (
    RuntimeCheckableImmutableMapping[str, ValueT]
)
type MutablePortableMapping[ValueT: MutablePortableData = MutablePortableData] = (
    RuntimeCheckableMutableMapping[str, ValueT]
)
type PortableMapping = ImmutablePortableMapping | MutablePortableMapping
type ImmutablePortableData = (
    PortableScalar | ImmutablePortableSequence | ImmutablePortableMapping
)
type MutablePortableData = (
    PortableScalar | MutablePortableSequence | MutablePortableMapping
)
type PortableData = ImmutablePortableData | MutablePortableData
type OptionalImmutablePortableData = ImmutablePortableData | NoPortableData
type OptionalMutablePortableData = MutablePortableData | NoPortableData
type OptionalPortableData = OptionalImmutablePortableData | OptionalMutablePortableData


def is_portable_scalar(value: Any, /) -> TypeGuard[PortableScalar]:
    """
    Check that a value is a portable data scalar.
    """
    return value is None or isinstance(value, _portable_scalar_types)


def freeze_portable_data(
    data: OptionalPortableData, /
) -> OptionalImmutablePortableData:
    """
    Make portable data frozen (immutable).
    """
    if data is NoPortableData or is_portable_scalar(data):
        return data
    if is_runtime_checkable_sequence(data):
        return tuple(map(freeze_portable_data, data))
    if is_runtime_checkable_mapping(data):
        return FrozenDict({
            key: freeze_portable_data(value) for key, value in data.items()
        })
    raise Unreachable


def unfreeze_portable_data(
    data: OptionalPortableData, /
) -> OptionalMutablePortableData:
    """
    Make portable data unfrozen (mutable).
    """
    if data is NoPortableData or is_portable_scalar(data):
        return data
    if is_runtime_checkable_sequence(data):
        return list(map(unfreeze_portable_data, data))
    if is_runtime_checkable_mapping(data):
        return {key: unfreeze_portable_data(value) for key, value in data.items()}
    raise Unreachable


class Porter[DataT, PortableDataT: PortableData = PortableData](metaclass=ABCMeta):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, data: PortableData, /) -> DataT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: DataT, /) -> PortableDataT:
        """
        Dump data to its portable form.
        """


class KeyedPorter[DataT, PortableDataT: PortableData = PortableData](
    Porter[DataT, PortableDataT]
):
    """
    An object capable of dumping and loading data to and from portable data and a paired primary key.
    """

    @abstractmethod
    def load_keyed(self, key: str, data: PortableData, /) -> DataT:
        """
        Create a new data instance from portable data and a portable primary key.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump_keyed(self, data: DataT, /) -> tuple[str, PortableData]:
        """
        Dump the data to portable data and a portable primary key.

        :raises betty.portable.error.NotDumpable: Raised if any part of the data is not portable.
        """
