"""
Key-value stores that do nothing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Self, final, override

from betty.store import StoreItem, StoreItemValueSetter, TransientStore

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@final
class NoOpStore(TransientStore[Any]):
    """
    A key-value store that does nothing.
    """

    @override
    def with_scope(self, scope: str, /) -> Self:
        return self

    async def _setter(self, value: Any) -> None:
        pass

    @override
    async def has(self, key: str, /) -> bool:
        return False

    @override
    @asynccontextmanager
    async def hasset(
        self, key: str, /
    ) -> AsyncGenerator[StoreItemValueSetter[Any] | None]:
        yield self._setter
        return

    @override
    async def get(self, key: str, /) -> StoreItem[Any] | None:
        return None

    @override
    async def set(
        self,
        key: str,
        value: Any,
        *,
        modified: float | None = None,
    ) -> None:
        return

    @override
    @asynccontextmanager
    async def getset(
        self, key: str, /
    ) -> AsyncGenerator[StoreItemValueSetter[Any] | StoreItem[Any]]:
        yield self._setter
        return

    @override
    async def clear(self) -> None:
        return

    @override
    async def delete(self, key: str, /) -> None:
        return
