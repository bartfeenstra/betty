from __future__ import annotations

from typing import TypeVar, Sequence, Mapping, overload, Literal, Generic

from typing_extensions import TypeAlias

from betty.app import App

T = TypeVar('T')
U = TypeVar('U')


class Void:
    pass


DumpType: TypeAlias = 'bool | int | float | str | None | list | dict'
DumpTypeT = TypeVar('DumpTypeT', bound=DumpType)

Dump: TypeAlias = 'bool | int | float | str | None | Sequence[Dump] | Mapping[str, Dump]'
DumpT = TypeVar('DumpT', bound=Dump)
DumpU = TypeVar('DumpU', bound=Dump)

VoidableDump: TypeAlias = 'DumpT | type[Void]'

ListDump: TypeAlias = list[DumpT]

DictDump: TypeAlias = dict[str, DumpT]

_VoidableItemListDump: TypeAlias = list[VoidableDump[DumpT]]

_VoidableItemDictDump: TypeAlias = dict[str, VoidableDump[DumpT]]

VoidableListDump: TypeAlias = '_VoidableItemListDump[DumpT] | type[Void]'

VoidableDictDump: TypeAlias = '_VoidableItemDictDump[DumpT] | type[Void]'


@overload
def minimize(dump: _VoidableItemListDump[DumpT], voidable: Literal[True] = True) -> VoidableDump[ListDump[DumpT]]:
    pass


@overload
def minimize(dump: _VoidableItemListDump[DumpT], voidable: Literal[False]) -> ListDump[DumpT]:
    pass


@overload
def minimize(dump: _VoidableItemDictDump[DumpT], voidable: Literal[True] = True) -> VoidableDump[DictDump[DumpT]]:
    pass


@overload
def minimize(dump: _VoidableItemDictDump[DumpT], voidable: Literal[False]) -> DictDump[DumpT]:
    pass


@overload
def minimize(dump: VoidableDump[DumpT], voidable: bool = True) -> VoidableDump[DumpT]:
    pass


def minimize(
    dump: VoidableDump[DumpT] | _VoidableItemListDump[DumpT] | _VoidableItemDictDump[DumpT],
    voidable: bool = True,
) -> VoidableDump[DumpT]:
    if isinstance(dump, (Sequence, Mapping)) and not isinstance(dump, str):
        minimized_dump: ListDump[DumpT] | DictDump[DumpT]
        if isinstance(dump, Sequence):
            minimized_dump = [
                value  # type: ignore[misc]
                for value
                in dump
                if value is not Void
            ]
        else:
            minimized_dump = {
                key: value  # type: ignore[misc]
                for key, value
                in dump.items()
                if value is not Void
            }
        if voidable and not len(minimized_dump):
            return minimized_dump  # type: ignore[return-value]
        return Void
    return dump  # type: ignore[return-value]


def none_to_void(value: VoidableDump[DumpT]) -> DumpT:
    return None if value is Void else value  # type: ignore[return-value]


def void_to_none(value: VoidableDump[DumpT]) -> VoidableDump[DumpT]:
    return Void if value is None else value  # type: ignore[redundant-expr]


def void_to_dict(
    value: VoidableDictDump[DumpT],
) -> _VoidableItemDictDump[DumpT]:
    return {} if value is Void else value  # type: ignore[return-value]


class Dumpable(Generic[DumpT]):
    def dump(self, app: App) -> VoidableDump[DumpT]:
        return Void
