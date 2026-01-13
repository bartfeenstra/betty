"""
The (de)serialization API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import Self, TypeAlias, TypeVar, final

from betty.exception import HumanFacingException

SerializedData: TypeAlias = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence["SerializedData"]
    | MutableMapping[str, "SerializedData"]
)
"""
Serialized data.

Data of this type is portable and can easily be persisted or transmitted.
"""


_SerializedDataT = TypeVar("_SerializedDataT", bound=SerializedData)


SerializedSequence: TypeAlias = MutableSequence[_SerializedDataT]
"""
A sequence of serialized data.
"""


SerializedMapping: TypeAlias = MutableMapping[str, _SerializedDataT]
"""
A key-value mapping of serialized data.

Keys are strings.
"""


@final
class NotDumpable(HumanFacingException):
    """
    Raised when data cannot be dumped due to runtime circumstances.
    """


class Serializable(ABC):
    """
    A class that can (de)serialize itself.
    """

    @classmethod
    @abstractmethod
    def load(cls, serialized: SerializedData, /) -> Self:
        """
        Create a new instance from ``serialized``.

        :raises betty.exception.HumanFacingException: Raised if the serialized data is invalid.
        """

    @abstractmethod
    def dump(self) -> SerializedData:
        """
        Produce a serialized data dump of ``self``.
        """
