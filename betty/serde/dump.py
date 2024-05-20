"""
Provide a serialization API.
"""

from __future__ import annotations

from typing import TypeVar, Sequence, Mapping, overload, Literal, TypeAlias, Any

T = TypeVar("T")
U = TypeVar("U")


class Void:
    """
    A sentinel that describes the absence of a value.

    Using this sentinel allows for actual values to be ``None``. Like ``None``,
    ``Void`` is only ever used through its type, and never instantiated.
    """

    def __new__(cls):  # pragma: no cover  # noqa D102
        raise RuntimeError("The Void sentinel cannot be instantiated.")


#: The Python types that define a serialized dump.
DumpType: TypeAlias = bool | int | float | str | None | list["Dump"] | dict[str, "Dump"]
DumpTypeT = TypeVar("DumpTypeT", bound=DumpType)

#: A serialized dump.
Dump: TypeAlias = (
    bool | int | float | str | None | Sequence["Dump"] | Mapping[str, "Dump"]
)
DumpT = TypeVar("DumpT", bound=Dump)
DumpU = TypeVar("DumpU", bound=Dump)

#: A serialized dump that may be :py:class:`betty.serde.dump.Void`.
VoidableDump: TypeAlias = Dump | type[Void]
VoidableDumpT = TypeVar("VoidableDumpT", bound=VoidableDump)
VoidableDumpU = TypeVar("VoidableDumpU", bound=VoidableDump)

#: A dump which is a list whose values are serialized dumps.
ListDump: TypeAlias = list[DumpT]

#: A dump which is a dictionary whose keys are strings and values are serialized dumps.
DictDump: TypeAlias = dict[str, DumpT]

#: A dump which is a list whose values are serialized dumps, or that may be :py:class:`betty.serde.dump.Void`
VoidableListDump: TypeAlias = list[VoidableDumpT]

#: A dump which is a dictionary whose keys are strings and values are serialized dumps, or that may be :py:class:`betty.serde.dump.Void`
VoidableDictDump: TypeAlias = dict[str, VoidableDumpT]

_MinimizableDump: TypeAlias = (
    VoidableDump | VoidableListDump[VoidableDumpT] | VoidableDictDump[VoidableDumpT]
)


@overload
def minimize(
    dump: _MinimizableDump[VoidableDump], voidable: Literal[True] = True
) -> VoidableDump:
    pass  # pragma: no cover


@overload
def minimize(dump: _MinimizableDump[VoidableDump], voidable: Literal[False]) -> Dump:
    pass  # pragma: no cover


def minimize(
    dump: _MinimizableDump[VoidableDump], voidable: bool = True
) -> VoidableDump:
    """
    Minimize a configuration dump by removing any Void configurationfrom sequences and mappings.
    """
    if isinstance(dump, (Sequence, Mapping)) and not isinstance(dump, str):
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
    dump: DictDump[Dump], key: str, default_type: type[dict[Any, Any]]
) -> DictDump[Dump]:
    pass  # pragma: no cover


@overload
def dump_default(
    dump: DictDump[Dump], key: str, default_type: type[list[Any]]
) -> ListDump[Dump]:
    pass  # pragma: no cover


def dump_default(dump, key, default_type):
    """
    Add a key and value to a dump, if the key does not exist yet.
    """
    try:
        assert isinstance(dump[key], default_type)
    except KeyError:
        dump[key] = default_type()
    return dump[key]  # type: ignore[return-value]


class Dumpable:
    """
    Instances can be dumped to serializable data.
    """

    def dump(self) -> VoidableDump:
        """
        Dump this instance to a portable format.
        """
        raise NotImplementedError(repr(self))
