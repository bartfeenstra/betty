"""
Persistent key-value stores backed by the file system.
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

from betty.file import read, write
from betty.hashid import hashid
from betty.pathlib import resolve_path
from betty.store import StoreItem, StoreItemValueSetter, TransientStore
from betty.stores._base import _CommonStoreBase, _CommonStoreBaseState
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence
    from pathlib import Path

    from betty.pathlib import StrPath


class _FileStoreItem[ItemValueT](StoreItem[ItemValueT]):
    __slots__ = "_modified", "_path"

    def __init__(
        self,
        modified: float,
        path: StrPath,
    ):
        self._modified = modified
        self._path = path

    @override
    @property
    def modified(self) -> int | float:
        return self._modified

    @override
    async def value(self) -> ItemValueT:
        return await self._load_value(await read(self._path, mode="rb"))

    @abstractmethod
    async def _load_value(self, value_bytes: bytes) -> ItemValueT:
        pass


@final
class _PickledFileStoreItem[ItemValueT](_FileStoreItem[ItemValueT]):
    @override
    async def _load_value(self, value_bytes: bytes) -> ItemValueT:
        return loads(value_bytes)


@final
class _BinaryFileStoreItem(_FileStoreItem[bytes]):
    @override
    async def _load_value(self, value_bytes: bytes) -> bytes:
        return value_bytes


class _FileStore[ItemValueT](_CommonStoreBase[ItemValueT]):
    _item_cls: type[_FileStoreItem[ItemValueT]]

    def __init__(
        self,
        directory: StrPath,
        *,
        scopes: Sequence[str] = (),
        state: _CommonStoreBaseState | None = None,
    ):
        super().__init__(scopes=scopes, state=state)
        self._root = resolve_path(directory)

    @override
    def with_scope(self, scope: str, /) -> Self:
        return type(self)(
            self._root,
            scopes=(*self._scopes, scope),
            state=_CommonStoreBaseState(self._lock, self._item_ledger),
        )

    def _file(self, key: str, suffix: str | None = None) -> Path:
        file = self._path / hashid(key)
        if suffix is not None:
            assert suffix.startswith(".")
            file = file.parent / (file.name + suffix)
        return file

    @abstractmethod
    def _dump_value(self, value: ItemValueT) -> bytes:
        pass

    @override
    async def has(self, key: str, *, suffix: str | None = None) -> bool:
        return await to_thread(self._file(key, suffix).exists)

    @override
    async def get(
        self, key: str, *, suffix: str | None = None
    ) -> StoreItem[ItemValueT] | None:
        try:
            file = self._file(key, suffix)
            return self._item_cls(await to_thread(getmtime, file), file)
        except OSError:
            return None

    @override
    async def set(
        self,
        key: str,
        value: ItemValueT,
        *,
        suffix: str | None = None,
        modified: float | None = None,
    ) -> None:
        value_bytes = self._dump_value(value)
        file = self._file(key, suffix)
        try:
            await self._write(file, value_bytes, modified)
        except FileNotFoundError:
            await to_thread(file.parent.mkdir, exist_ok=True, parents=True)
            await self._write(file, value_bytes, modified)

    async def _write(
        self, file: StrPath, value: bytes, modified: float | None = None
    ) -> None:
        await write(file, value, mode="wb")
        if modified is not None:
            await asyncio.to_thread(utime, file, (modified, modified))

    @property
    def _path(self) -> Path:
        return self._root.joinpath(*self._scopes)

    @override
    @asynccontextmanager
    async def hasset(
        self, key: str, *, suffix: str | None = None
    ) -> AsyncIterator[StoreItemValueSetter[ItemValueT] | None]:
        if await self.has(key, suffix=suffix):
            yield None
            return
        async with self._item_ledger.ledger(key):
            if await self.has(key, suffix=suffix):
                yield None
                return
            yield partial(self.set, key, suffix=suffix)
        return

    @override
    @asynccontextmanager
    async def getset(
        self, key: str, *, suffix: str | None = None
    ) -> AsyncIterator[StoreItemValueSetter[ItemValueT] | StoreItem[ItemValueT]]:
        if item := await self.get(key):
            yield item
            return
        async with self._item_ledger.ledger(key):
            if item := await self.get(key, suffix=suffix):
                yield item
                return
            yield partial(self.set, key, suffix=suffix)
        return


class _TransientFileStore[ItemValueT](
    _FileStore[ItemValueT], TransientStore[ItemValueT]
):
    @override
    async def clear(self) -> None:
        await asyncio.to_thread(shutil.rmtree, self._path, ignore_errors=True)

    @override
    async def delete(self, key: str, *, suffix: str | None = None) -> None:
        with suppress(FileNotFoundError):
            await to_thread(self._file(key, suffix).unlink)


class _PickledFileStore[ItemValueT](_FileStore[ItemValueT]):
    _item_cls = _PickledFileStoreItem

    @override
    def _dump_value(self, value: ItemValueT) -> bytes:
        return dumps(value)


@final
@threadsafe
class PickledFileStore[ItemValueT](_PickledFileStore[ItemValueT]):
    """
    A key-value store that pickles values and persists them to files.
    """


@final
@threadsafe
class TransientPickledFileStore[ItemValueT](
    _PickledFileStore[ItemValueT], _TransientFileStore[ItemValueT]
):
    """
    A transient key-value store that pickles values and persists them to files.
    """


class _BinaryFileStore(_FileStore[bytes]):
    _item_cls = _BinaryFileStoreItem

    @override
    def _dump_value(self, value: bytes) -> bytes:
        return value

    @property
    def directory(self) -> Path:
        """
        The path to the store's root directory.
        """
        return self._path

    def file(self, key: str, suffix: str | None = None, /) -> Path:
        """
        Get the file path for an item with the given key.

        The item itself may or may not exist.
        """
        return self._file(key, suffix)


@final
@threadsafe
class BinaryFileStore(_BinaryFileStore):
    """
    A key-value store that persists bytes values to binary files.
    """


@final
@threadsafe
class TransientBinaryFileStore(_BinaryFileStore, _TransientFileStore[bytes]):
    """
    A transient key-value store that persists bytes values to binary files.
    """
