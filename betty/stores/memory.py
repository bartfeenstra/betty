"""
Key-value stores that store items in volatile memory.
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from typing import Self, final, override

from betty.store import StoreItem, TransientStore
from betty.stores._base import _CommonStoreBase, _CommonStoreBaseState, _StaticStoreItem
from betty.typing import threadsafe

type _MemoryStoreData[ItemValueT] = MutableMapping[
    tuple[str, ...],
    StoreItem[ItemValueT] | None | _MemoryStoreData[ItemValueT],
]


@final
@dataclass(frozen=True)
class _MemoryStoreState(_CommonStoreBaseState):
    data: _MemoryStoreData


class _MemoryStore[ItemValueT](_CommonStoreBase[ItemValueT]):
    _data: _MemoryStoreData[ItemValueT]

    def __init__(
        self, *, scopes: Sequence[str] = (), state: _MemoryStoreState | None = None
    ):
        super().__init__(scopes=scopes, state=state)
        if state is None:
            self._data = {}
        else:
            self._data = state.data

    @override
    def with_scope(self, scope: str, /) -> Self:
        return type(self)(
            scopes=(*self._scopes, scope),
            state=_MemoryStoreState(self._lock, self._item_ledger, self._data),
        )

    def _item_key(self, key: str) -> tuple[str, ...]:
        return *self._scopes, key

    @override
    async def get(self, key: str, /) -> StoreItem[ItemValueT] | None:
        item = self._data.get(self._item_key(key), None)
        if isinstance(item, StoreItem):
            return item  # ty:ignore[invalid-return-type]
        return None

    @override
    async def set(
        self, key: str, value: ItemValueT, *, modified: float | None = None
    ) -> None:
        self._data[self._item_key(key)] = _StaticStoreItem(value, modified)


@final
@threadsafe
class MemoryStore[ItemValueT](_MemoryStore[ItemValueT]):
    """
    A key-value store that stores items in volatile memory.
    """


@final
@threadsafe
class TransientMemoryStore[ItemValueT](
    _MemoryStore[ItemValueT], TransientStore[ItemValueT]
):
    """
    A key-value store that stores items in volatile memory.
    """

    @override
    async def clear(self) -> None:
        self._data.clear()

    @override
    async def delete(self, key: str, /) -> None:
        self._data.pop(self._item_key(key), None)
