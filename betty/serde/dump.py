"""
An API to produce serializable data dumps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import TypeAlias, TypeVar, final

from betty.exception import HumanFacingException

Dump: TypeAlias = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence["Dump"]
    | MutableMapping[str, "Dump"]
)
"""
A serialized dump.
"""

_DumpT = TypeVar("_DumpT", bound=Dump)

DumpSequence: TypeAlias = MutableSequence[_DumpT]
"""
A dump which is a sequence whose values are serialized dumps.
"""

DumpMapping: TypeAlias = MutableMapping[str, _DumpT]
"""
A dump which is a mapping whose keys are strings and values are serialized dumps.
"""


class Dumpable(ABC):
    """
    Instances can be produce serialized data dumps of ``self``.
    """

    @abstractmethod
    def dump(self) -> Dump:
        """
        Produce a serialized data dump of ``self``.
        """


@final
class NotDumpable(HumanFacingException):
    """
    Raised when a :py:class:`betty.serde.dump.Dumpable.dump` implementation cannot dump any data due to runtime circumstances.
    """
