from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING, override

from betty.concurrent import Ledger, ThreadSafeLock
from betty.store import Store, StoreItem, StoreItemValueSetter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence


class _StaticStoreItem[ItemValueT](StoreItem[ItemValueT]):
    __slots__ = "_modified", "_value"

    def __init__(
        self,
        value: ItemValueT,
        modified: float | None = None,
    ):
        self._value = value
        self._modified = (
            datetime.now(tz=UTC).timestamp() if modified is None else modified
        )

    @override
    async def value(self) -> ItemValueT:
        return self._value

    @override
    @property
    def modified(self) -> int | float:
        return self._modified


@dataclass(frozen=True)
class _CommonStoreBaseState:
    lock: ThreadSafeLock
    item_ledger: Ledger


class _CommonStoreBase[ItemValueT](Store[ItemValueT]):
    def __init__(
        self,
        *,
        scopes: Sequence[str] = (),
        state: _CommonStoreBaseState | None = None,
    ):
        self._scopes = scopes
        if state is not None:
            self._lock = state.lock
            self._item_ledger = state.item_ledger
        else:
            self._lock = ThreadSafeLock()
            self._item_ledger = Ledger(self._lock)

    @override
    @asynccontextmanager
    async def hasset(
        self, key: str, /
    ) -> AsyncIterator[StoreItemValueSetter[ItemValueT] | None]:
        if await self.has(key):
            yield None
            return
        async with self._item_ledger.ledger(key):
            if await self.has(key):
                yield None
            yield partial(self.set, key)
        return

    @override
    @asynccontextmanager
    async def getset(
        self, key: str, /
    ) -> AsyncIterator[StoreItemValueSetter[ItemValueT] | StoreItem[ItemValueT]]:
        if item := await self.get(key):
            yield item
            return
        async with self._item_ledger.ledger(key):
            if item := await self.get(key):
                yield item
                return
            yield partial(self.set, key)
        return
