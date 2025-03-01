import multiprocessing
from collections.abc import Sequence, AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

from typing_extensions import override

from betty.cache.memory import MemoryCache
from betty.test_utils.cache import ProcesssafeCacheTestBase


class TestMemoryCache(ProcesssafeCacheTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncIterator[MemoryCache[Any]]:
        with multiprocessing.Manager() as manager:
            yield MemoryCache(scopes=scopes, manager=manager)

    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}
