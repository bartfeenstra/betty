from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, override

from betty.stores.memory import MemoryStore, TransientMemoryStore
from betty.test_utils.store import StoreTestBase, TransientStoreTestBase


class _TestMemoryStore(StoreTestBase[Any]):
    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}


class TestMemoryStore(_TestMemoryStore):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[MemoryStore[Any]]:
        yield MemoryStore(scopes=scopes)


class TestTransientMemoryStore(_TestMemoryStore, TransientStoreTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[TransientMemoryStore[Any]]:
        yield TransientMemoryStore(scopes=scopes)
