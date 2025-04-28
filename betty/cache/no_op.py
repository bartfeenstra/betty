"""
Provide no-op caching.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Self,
    TypeAlias,
    final,
    overload,
)

from typing_extensions import override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.typing import processsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType

_GetSet: TypeAlias = tuple[
    CacheItem[Any] | None,
    CacheItemValueSetter[Any] | None,
]


class _NoOpGetSet:
    def __init__(self, has_setter: bool):
        self._has_setter = has_setter

    async def __aenter__(self) -> _GetSet:
        return None, self._set if self._has_setter else None

    async def _set(self, value: Any) -> None:
        return

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return


@final
@processsafe
class NoOpCache(Cache[Any]):
    """
    Provide a cache that does nothing.
    """

    @override
    def with_scope(self, scope: str) -> Self:
        return self

    @override
    @asynccontextmanager
    async def get(self, cache_item_id: str) -> AsyncIterator[CacheItem[Any] | None]:
        yield None

    @override
    async def set(
        self,
        cache_item_id: str,
        value: Any,
        *,
        modified: int | float | None = None,
    ) -> None:
        return

    @overload
    def getset(
        self, cache_item_id: str
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[Any] | None,
            CacheItemValueSetter[Any],
        ]
    ]:
        pass

    @overload
    def getset(
        self, cache_item_id: str, *, wait: Literal[False] = False
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[Any] | None,
            CacheItemValueSetter[Any] | None,
        ]
    ]:
        pass

    @override
    def getset(
        self, cache_item_id: str, *, wait: bool = True
    ) -> AbstractAsyncContextManager[_GetSet]:
        return _NoOpGetSet(wait)

    @override
    async def delete(self, cache_item_id: str) -> None:
        return

    @override
    async def clear(self) -> None:
        return
