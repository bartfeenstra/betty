"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence

from typing_extensions import sentinel

type PortableScalar = None | bool | int | float | str
# @todo Add frozendict
# @todo
# @todo
# @todo Should we keep globals with (list, tuple) and (dict,)/(dict, frozendict) in betty.typing or somewhere else,
# @todo so we won't constantly have to check for Python 3.15 everywhere?
# @todo
# @todo
type FrozenPortableData = (
    PortableScalar | tuple[PortableData, ...] | Mapping[str, PortableData]
)


type UnfrozenPortableData = (
    PortableScalar | Sequence[PortableData] | Mapping[str, PortableData]
)

type PortableData = FrozenPortableData | UnfrozenPortableData
"""
Portable data.

Data of this type is portable and can easily be persisted or transmitted.
"""


NoPortableData = sentinel("NoPortableData")


type OptionalPortableData[PortableDataT: PortableData] = PortableDataT | NoPortableData


type PortableSequence = Sequence[PortableData]
"""
A sequence of portable data.
"""


type PortableMapping = Mapping[str, PortableData]
"""
A key-value mapping of portable data.

Keys are strings.
"""


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
