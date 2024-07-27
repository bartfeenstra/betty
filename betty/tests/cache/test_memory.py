from collections.abc import Sequence, AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

from typing_extensions import override

from betty.cache.memory import MemoryCache
from betty.test_utils.cache import CacheTestBase


class TestMemoryCache(CacheTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncIterator[MemoryCache[Any]]:
        yield MemoryCache(scopes=scopes)

    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}
