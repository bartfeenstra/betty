"""
An API to produce serializable data dumps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence, Sequence, Mapping
from typing import overload, Literal, TypeAlias, Generic

from typing_extensions import TypeVar

from betty.typing import Void, Voidable

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
_DumpT = TypeVar("_DumpT", bound=Dump, default=Dump)

#: A dump which is a sequence whose values are serialized dumps.
DumpSequence: TypeAlias = MutableSequence[_DumpT]

#: A dump which is a mapping whose keys are strings and values are serialized dumps.
DumpMapping: TypeAlias = MutableMapping[str, _DumpT]


@overload
def minimize(
    dump: Sequence[Voidable[Dump]], voidable: Literal[False] = False
) -> DumpSequence[Dump]:
    pass


@overload
def minimize(
    dump: Sequence[Voidable[Dump]], voidable: bool
) -> Voidable[DumpSequence[Dump]]:
    pass


@overload
def minimize(
    dump: Mapping[str, Voidable[Dump]], voidable: Literal[False] = False
) -> DumpMapping[Dump]:
    pass


@overload
def minimize(
    dump: Mapping[str, Voidable[Dump]], voidable: bool
) -> Voidable[DumpMapping[Dump]]:
    pass


def minimize(
    dump: Sequence[Voidable[Dump]] | Mapping[str, Voidable[Dump]],
    voidable: bool = False,
) -> Voidable[DumpSequence[Dump] | DumpMapping[Dump]]:
    """
    Minimize a configuration dump by removing any :py:class:'betty.typing.Void' values from sequences and mappings.
    """
    if isinstance(dump, Sequence):
        dump = [value for value in dump if value is not Void]
        for key in reversed(range(len(dump))):
            if dump[key] is Void:
                del dump[key]
    if isinstance(dump, Mapping):
        dump = {key: value for key, value in dump.items() if value is not Void}
    if len(dump) or not voidable:
        return dump  # type: ignore[return-value]
    return Void


class Dumpable(ABC, Generic[_DumpT]):
    """
    Instances can be produce serialized data dumps of ``self``.
    """

    @abstractmethod
    def dump(self) -> Voidable[_DumpT]:
        """
        Produce a serialized data dump of ``self``.
        """
        pass
