"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import Self, TypeAlias

from typing_extensions import TypeVar

PortableData: TypeAlias = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence["PortableData"]
    | MutableMapping[str, "PortableData"]
)
"""
Portable data.

Data of this type is portable and can easily be persisted or transmitted.
"""


_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


PortableSequence: TypeAlias = MutableSequence[_PortableDataT]
"""
A sequence of portable data.
"""


PortableMapping: TypeAlias = MutableMapping[str, _PortableDataT]
"""
A key-value mapping of portable data.

Keys are strings.
"""


class Portable(ABC):
    """
    A class that can be dumped to and loaded from portable data.
    """

    @classmethod
    @abstractmethod
    def load(cls, portable: PortableData, /) -> Self:
        """
        Create a new instance from ``portable``.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump(self) -> PortableData:
        """
        Produce a portable data dump of ``self``.

        :raises betty.portable.error.NotPortable: Raised if any part of the data is not portable.
        """
