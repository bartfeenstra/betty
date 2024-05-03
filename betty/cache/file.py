"""
Provide caching that persists cache items to files.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import Sequence
from contextlib import suppress
from os import utime
from pathlib import Path
from pickle import dumps, loads
from typing import Generic, Self

import aiofiles
from aiofiles.ospath import getmtime

from betty.cache import CacheItem, CacheItemValueContraT, CacheItemValueCoT
from betty.cache._base import _CommonCacheBase
from betty.hashid import hashid
from betty.locale import Localizer


class _FileCacheItem(CacheItem[CacheItemValueCoT], Generic[CacheItemValueCoT]):
    __slots__ = "_modified", "_path"

    def __init__(
        self,
        modified: int | float,
        path: Path,
    ):
        self._modified = modified
        self._path = path

    @property
    def modified(self) -> int | float:
        return self._modified

    async def value(self) -> CacheItemValueCoT:
        async with aiofiles.open(self._path, "rb") as f:
            value_bytes = await f.read()
        return await self._load_value(value_bytes)

    async def _load_value(self, value_bytes: bytes) -> CacheItemValueCoT:
        raise NotImplementedError


class _PickledFileCacheItem(
    _FileCacheItem[CacheItemValueCoT], Generic[CacheItemValueCoT]
):
    async def _load_value(self, value_bytes: bytes) -> CacheItemValueCoT:
        return loads(value_bytes)  # type: ignore[no-any-return]


class _BinaryFileCacheItem(_FileCacheItem[bytes]):
    async def _load_value(self, value_bytes: bytes) -> bytes:
        return value_bytes


class _FileCache(
    _CommonCacheBase[CacheItemValueContraT], Generic[CacheItemValueContraT]
):
    """
    Provide a cache that persists cache items on a file system.
    """

    _cache_item_cls: type[_FileCacheItem[CacheItemValueContraT]]

    def __init__(
        self,
        localizer: Localizer,
        cache_directory_path: Path,
        *,
        scopes: Sequence[str] | None = None,
    ):
        super().__init__(localizer, scopes=scopes)
        self._root_path = cache_directory_path

    def _with_scope(self, scope: str) -> Self:
        return type(self)(
            self._localizer, self._root_path, scopes=(*self._scopes, scope)
        )

    def _cache_item_file_path(self, cache_item_id: str) -> Path:
        return self._path / hashid(cache_item_id)

    def _dump_value(self, value: CacheItemValueContraT) -> bytes:
        raise NotImplementedError

    async def _get(self, cache_item_id: str) -> CacheItem[CacheItemValueContraT] | None:
        try:
            cache_item_file_path = self._cache_item_file_path(cache_item_id)
            return self._cache_item_cls(
                await getmtime(cache_item_file_path),
                cache_item_file_path,
            )
        except OSError:
            return None

    async def _set(
        self,
        cache_item_id: str,
        value: CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        value = self._dump_value(value)
        cache_item_file_path = self._cache_item_file_path(cache_item_id)
        try:
            await self._write(cache_item_file_path, value, modified)
        except FileNotFoundError:
            await aiofiles.os.makedirs(cache_item_file_path.parent, exist_ok=True)
            await self._write(cache_item_file_path, value, modified)

    async def _write(
        self,
        cache_item_file_path: Path,
        value: bytes,
        modified: int | float | None = None,
    ) -> None:
        async with aiofiles.open(cache_item_file_path, "wb") as f:
            await f.write(value)
        if modified is not None:
            await asyncio.to_thread(utime, cache_item_file_path, (modified, modified))

    async def _delete(self, cache_item_id: str) -> None:
        with suppress(FileNotFoundError):
            await aiofiles.os.remove(self._cache_item_file_path(cache_item_id))

    async def _clear(self) -> None:
        with suppress(FileNotFoundError):
            await asyncio.to_thread(shutil.rmtree, self._path)

    @property
    def _path(self) -> Path:
        return self._root_path.joinpath(*self._scopes)


class PickledFileCache(
    _FileCache[CacheItemValueContraT], Generic[CacheItemValueContraT]
):
    """
    Provide a cache that pickles values and persists them to files.
    """

    _cache_item_cls = _PickledFileCacheItem

    def _dump_value(self, value: CacheItemValueContraT) -> bytes:
        return dumps(value)


class BinaryFileCache(_FileCache[bytes]):
    """
    Provide a cache that persists bytes values to binary files.
    """

    _cache_item_cls = _BinaryFileCacheItem

    def _dump_value(self, value: bytes) -> bytes:
        return value

    @property
    def path(self) -> Path:
        return self._path

    def cache_item_file_path(self, cache_item_id: str) -> Path:
        return self._cache_item_file_path(cache_item_id)
