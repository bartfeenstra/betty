"""
Provide a serialization API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import TypeVar, overload, Literal, TypeAlias

from betty.typing import Void

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

#: A serialized dump that may be :py:class:`betty.typing.Void`.
VoidableDump: TypeAlias = Dump | type[Void]
_VoidableDumpT = TypeVar("_VoidableDumpT", bound=VoidableDump)

#: A dump which is a sequence whose values are serialized dumps.
DumpSequence: TypeAlias = MutableSequence[_DumpT]

#: A dump which is a mapping whose keys are strings and values are serialized dumps.
DumpMapping: TypeAlias = MutableMapping[str, _DumpT]

#: A dump which is a sequence whose values are serialized dumps, or that may be :py:class:`betty.serde.dump.Void`
VoidableDumpSequence: TypeAlias = MutableSequence[_VoidableDumpT]

#: A dump which is a mapping whose keys are strings and values are serialized dumps, or that may be :py:class:`betty.serde.dump.Void`
VoidableDumpMapping: TypeAlias = MutableMapping[str, _VoidableDumpT]

_MinimizableDump: TypeAlias = (
    VoidableDump
    | VoidableDumpSequence[_VoidableDumpT]
    | VoidableDumpMapping[_VoidableDumpT]
)


@overload
def minimize(
    dump: _MinimizableDump[VoidableDump], voidable: Literal[True] = True
) -> VoidableDump:
    pass


@overload
def minimize(dump: _MinimizableDump[VoidableDump], voidable: Literal[False]) -> Dump:
    pass


def minimize(
    dump: _MinimizableDump[VoidableDump], voidable: bool = True
) -> VoidableDump:
    """
    Minimize a configuration dump by removing any Void configurationfrom sequences and mappings.
    """
    if isinstance(dump, (MutableSequence, MutableMapping)):
        if isinstance(dump, MutableSequence):
            dump = [value for value in dump if value is not Void]
            for key in reversed(range(len(dump))):
                if dump[key] is Void:
                    del dump[key]
        if isinstance(dump, MutableMapping):
            dump = {key: value for key, value in dump.items() if value is not Void}
        if len(dump) or not voidable:
            return dump  # type: ignore[return-value]
        return Void
    return dump


def void_none(value: VoidableDump) -> VoidableDump:
    """
    Passthrough a value, but convert Void to None.
    """
    return Void if value is None else value


def none_void(value: VoidableDump) -> VoidableDump:
    """
    Passthrough a value, but convert None to Void.
    """
    return None if value is Void else value


@overload
def dump_default(
    dump: DumpMapping[Dump], key: str, default_type: type[DumpMapping[Dump]]
) -> DumpMapping[Dump]:
    pass


@overload
def dump_default(
    dump: DumpMapping[Dump], key: str, default_type: type[DumpSequence[Dump]]
) -> DumpSequence[Dump]:
    pass


def dump_default(dump, key, default_type):
    """
    Add a key and value to a dump, if the key does not exist yet.
    """
    try:
        assert isinstance(dump[key], default_type)
    except KeyError:
        dump[key] = default_type()
    return dump[key]  # type: ignore[return-value]


class Dumpable(ABC):
    """
    Instances can be dumped to serializable data.
    """

    @abstractmethod
    def dump(self) -> VoidableDump:
        """
        Dump this instance to a portable format.
        """
        pass
