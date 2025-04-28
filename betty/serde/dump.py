"""
An API to produce serializable data dumps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import TypeAlias, TypeVar

#: A serialized dump.
Dump: TypeAlias = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence["Dump"]
    | MutableMapping[str, "Dump"]
)
_DumpT = TypeVar("_DumpT", bound=Dump)

#: A dump which is a sequence whose values are serialized dumps.
DumpSequence: TypeAlias = MutableSequence[_DumpT]

#: A dump which is a mapping whose keys are strings and values are serialized dumps.
DumpMapping: TypeAlias = MutableMapping[str, _DumpT]


class Dumpable(ABC):
    """
    Instances can be produce serialized data dumps of ``self``.
    """

    @abstractmethod
    def dump(self) -> Dump:
        """
        Produce a serialized data dump of ``self``.
        """
