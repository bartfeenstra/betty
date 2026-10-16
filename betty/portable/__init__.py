"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

import builtins
import sys
from abc import ABCMeta, abstractmethod
from typing import Final

from typing_extensions import sentinel

# @todo We keep duplicating some checks and definitions, especially these collection types.
# @todo Come up with a solution for immutable mappings on Python 3.14 and lower, otherwise we're blocked...
# @todo
# @todo
# @todo
_portable_mapping_types = (dict,)
if sys.version_info >= (3, 15):
    _portable_mapping_types = (*_portable_mapping_types, builtins.frozendict)
portable_mapping_types: Final[tuple[type, ...]] = _portable_mapping_types
portable_sequence_types: Final[tuple[type, ...]] = (list, tuple)
type PortableScalar = None | bool | int | float | str
type ImmutablePortableSequence[ValueT: ImmutablePortableData] = tuple[ValueT, ...]
type MutablePortableSequence[ValueT: MutablePortableData] = list[ValueT]
type PortableSequence[ValueT: PortableData] = (
    ImmutablePortableSequence[ValueT] | MutablePortableSequence[ValueT]
)
if sys.version_info >= (3, 15):
    type ImmutablePortableMapping[ValueT: ImmutablePortableData] = builtins.frozendict[
        str, ValueT
    ]
type MutablePortableMapping[ValueT: MutablePortableData] = dict[str, ValueT]
if sys.version_info >= (3, 15):
    type PortableMapping[ValueT: PortableData] = (
        ImmutablePortableMapping[ValueT] | MutablePortableMapping[ValueT]
    )
    type ImmutablePortableData = (
        PortableScalar | ImmutablePortableSequence | ImmutablePortableMapping
    )
else:
    # @todo How to support immutable mappings on Python 3.14 and lower?
    type PortableMapping[ValueT: PortableData] = MutablePortableMapping[ValueT]
    type ImmutablePortableData = PortableScalar | PortableSequence | PortableMapping
type MutablePortableData = (
    PortableScalar | MutablePortableSequence | MutablePortableMapping
)
type PortableData = ImmutablePortableData | MutablePortableData


NoPortableData = sentinel("NoPortableData")


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
