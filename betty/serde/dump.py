"""
An API to produce serializable data dumps.
"""

from __future__ import annotations

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


@final
class NotDumpable(HumanFacingException):
    """
    Raised when a data cannot be dumped due to runtime circumstances.
    """
