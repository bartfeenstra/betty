"""
Provide caching that persists cache items to files.
"""

from __future__ import annotations

import asyncio
import shutil
from abc import abstractmethod
from asyncio import to_thread
from contextlib import asynccontextmanager, suppress
from functools import partial
from os import utime
from os.path import getmtime
from pickle import dumps, loads
from typing import TYPE_CHECKING, Self, final, override

from betty.cache import CacheItem, CacheItemValueSetter
from betty.cache._base import _CommonCacheBase, _CommonCacheBaseState
from betty.file import read, write
from betty.hashid import hashid
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence
    from pathlib import Path


class _FileCacheItem[CacheItemValueT](CacheItem[CacheItemValueT]):
    __slots__ = "_modified", "_path"

    def __init__(
        self,
        modified: float,
        path: Path,
    ):
        self._modified = modified
        self._path = path

    @override
    @property
    def modified(self) -> int | float:
        return self._modified

    @override
    async def value(self) -> CacheItemValueT:
        return await self._load_value(await read(self._path, mode="rb"))

    @abstractmethod
    async def _load_value(self, value_bytes: bytes) -> CacheItemValueT:
        pass


@final
class _PickledFileCacheItem[CacheItemValueT](_FileCacheItem[CacheItemValueT]):
    @override
    async def _load_value(self, value_bytes: bytes) -> CacheItemValueT:
        return loads(value_bytes)


@final
class _BinaryFileCacheItem(_FileCacheItem[bytes]):
    @override
    async def _load_value(self, value_bytes: bytes) -> bytes:
        return value_bytes


class _FileCache[CacheItemValueT](_CommonCacheBase[CacheItemValueT]):
    """
    Provide a cache that persists cache items on a file system.
    """

    _cache_item_cls: type[_FileCacheItem[CacheItemValueT]]

    def __init__(
        self,
        cache_directory_path: Path,
        *,
        scopes: Sequence[str] = (),
        state: _CommonCacheBaseState | None = None,
    ):
        super().__init__(scopes=scopes, state=state)
        self._root_path = cache_directory_path

    @override
    def with_scope(self, scope: str, /) -> Self:
        return type(self)(
            self._root_path,
            scopes=(*self._scopes, scope),
            state=_CommonCacheBaseState(self._cache_lock, self._cache_item_lock_ledger),
        )

    def _cache_item_file_path(
        self, cache_item_id: str, suffix: str | None = None
    ) -> Path:
        cache_item_file_path = self._path / hashid(cache_item_id)
        if suffix is not None:
            assert suffix.startswith(".")
            cache_item_file_path = cache_item_file_path.parent / (
                cache_item_file_path.name + suffix
            )
        return cache_item_file_path

    @abstractmethod
    def _dump_value(self, value: CacheItemValueT) -> bytes:
        pass

    @override
    async def has(self, cache_item_id: str, *, suffix: str | None = None) -> bool:
        return await to_thread(self._cache_item_file_path(cache_item_id, suffix).exists)

    @override
    async def get(
        self, cache_item_id: str, *, suffix: str | None = None
    ) -> CacheItem[CacheItemValueT] | None:
        try:
            cache_item_file_path = self._cache_item_file_path(cache_item_id, suffix)
            return self._cache_item_cls(
                await to_thread(getmtime, cache_item_file_path),
                cache_item_file_path,
            )
        except OSError:
            return None

    @override
    async def set(
        self,
        cache_item_id: str,
        value: CacheItemValueT,
        *,
        suffix: str | None = None,
        modified: float | None = None,
    ) -> None:
        value_bytes = self._dump_value(value)
        cache_item_file_path = self._cache_item_file_path(cache_item_id, suffix)
        try:
            await self._write(cache_item_file_path, value_bytes, modified)
        except FileNotFoundError:
            await to_thread(
                cache_item_file_path.parent.mkdir, exist_ok=True, parents=True
            )
            await self._write(cache_item_file_path, value_bytes, modified)

    async def _write(
        self,
        cache_item_file_path: Path,
        value: bytes,
        modified: float | None = None,
    ) -> None:
        await write(cache_item_file_path, value, mode="wb")
        if modified is not None:
            await asyncio.to_thread(utime, cache_item_file_path, (modified, modified))

    @override
    async def delete(self, cache_item_id: str, *, suffix: str | None = None) -> None:
        with suppress(FileNotFoundError):
            await to_thread(self._cache_item_file_path(cache_item_id, suffix).unlink)

    @override
    async def clear(self) -> None:
        with suppress(FileNotFoundError):
            await asyncio.to_thread(shutil.rmtree, self._path)

    @property
    def _path(self) -> Path:
        return self._root_path.joinpath(*self._scopes)

    @override
    @asynccontextmanager
    async def hasset(
        self, cache_item_id: str, *, suffix: str | None = None
    ) -> AsyncIterator[CacheItemValueSetter[CacheItemValueT] | None]:
        if await self.has(cache_item_id, suffix=suffix):
            yield None
            return
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
            if await self.has(cache_item_id, suffix=suffix):
                yield None
                return
            yield partial(self.set, cache_item_id, suffix=suffix)
        return

    @override
    @asynccontextmanager
    async def getset(
        self, cache_item_id: str, *, suffix: str | None = None
    ) -> AsyncIterator[
        CacheItemValueSetter[CacheItemValueT] | CacheItem[CacheItemValueT]
    ]:
        if cache_item := await self.get(cache_item_id):
            yield cache_item
            return
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
            if cache_item := await self.get(cache_item_id, suffix=suffix):
                yield cache_item
                return
            yield partial(self.set, cache_item_id, suffix=suffix)
        return


@final
@threadsafe
class PickledFileCache[CacheItemValueT](_FileCache[CacheItemValueT]):
    """
    Provide a cache that pickles values and persists them to files.
    """

    _cache_item_cls = _PickledFileCacheItem

    @override
    def _dump_value(self, value: CacheItemValueT) -> bytes:
        return dumps(value)


@final
@threadsafe
class BinaryFileCache(_FileCache[bytes]):
    """
    Provide a cache that persists bytes values to binary files.
    """

    _cache_item_cls = _BinaryFileCacheItem

    @override
    def _dump_value(self, value: bytes) -> bytes:
        return value

    @property
    def path(self) -> Path:
        """
        The path to the cache's root directory.
        """
        return self._path

    def cache_item_file_path(
        self, cache_item_id: str, suffix: str | None = None, /
    ) -> Path:
        """
        Get the file path for a cache item with the given ID.

        The cache item itself may or may not exist.
        """
        return self._cache_item_file_path(cache_item_id, suffix)
