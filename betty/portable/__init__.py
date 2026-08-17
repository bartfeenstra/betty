"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping, MutableSequence

type PortableData = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence[PortableData]
    | MutableMapping[str, PortableData]
)
"""
Portable data.

Data of this type is portable and can easily be persisted or transmitted.
"""


type PortableSequence = MutableSequence[PortableData]
"""
A sequence of portable data.
"""


type PortableMapping = MutableMapping[str, PortableData]
"""
A key-value mapping of portable data.

Keys are strings.
"""


class Porter[DataT](metaclass=ABCMeta):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, data: PortableData, /) -> DataT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: DataT, /) -> PortableData:
        """
        Dump data to its portable form.
        """


class KeyedPorter[DataT](Porter[DataT]):
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
