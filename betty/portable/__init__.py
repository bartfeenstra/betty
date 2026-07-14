"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import Self

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


type PortableSequence[PortableDataT: PortableData] = MutableSequence[PortableDataT]
"""
A sequence of portable data.
"""


type PortableMapping[PortableDataT: PortableData] = MutableMapping[str, PortableDataT]
"""
A key-value mapping of portable data.

Keys are strings.
"""


class Portable[PortableDataT: PortableData](ABC):
    """
    A class that can be dumped to and loaded from portable data.
    """

    @classmethod
    @abstractmethod
    def load(cls, portable: PortableData, /) -> Self:
        """
        Create a new instance from portable data.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump(self) -> PortableDataT:
        """
        Dump the instance to portable data.

        :raises betty.portable.error.NotPortable: Raised if any part of the data is not portable.
        """


class Porter[DataClsT, PortableDataT: PortableData = PortableData](ABC):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, portable: PortableData, /) -> DataClsT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: DataClsT, /) -> PortableDataT:
        """
        Dump data to its portable form.
        """
