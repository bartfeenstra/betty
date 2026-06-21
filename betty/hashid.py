"""
Provides utilities to generate unique IDs through hashing.

This module MUST NOT be used for security purposes.
"""

from __future__ import annotations

from asyncio import to_thread
from hashlib import md5
from os import stat
from typing import TYPE_CHECKING

from betty.file import read

if TYPE_CHECKING:
    from betty.pathlib import StrPath


def _hashid_bytes(key: bytes, /) -> str:
    return md5(key, usedforsecurity=False).hexdigest()


def hashid(key: bytes | str, /) -> str:
    """
    Create a hash ID for a key.
    """
    if isinstance(key, str):
        key: bytes = key.encode()
    return _hashid_bytes(key)


def hashid_sequence(*keys: bytes | str) -> str:
    """
    Create a hash ID from a sequence of keys.
    """
    return hashid(":".join(map(hashid, keys)))


async def hashid_file_meta(file: StrPath, /) -> str:
    """
    Create a hash ID for a file based on its metadata.

    This function relies on the file path, size, and last modified time for uniqueness.
    File contents are ignored. This may be suitable for large files whose
    exact contents may not be very relevant in the context the ID is used in.
    """
    file_stat_result = await to_thread(stat, file)
    return hashid_sequence(
        str(file), str(file_stat_result.st_size), str(file_stat_result.st_mtime_ns)
    )


async def hashid_file_content(file: StrPath, /) -> str:
    """
    Create a hash ID for a file based on its contents.

    This function relies on the file path and contents for uniqueness.
    File contents must be loaded into memory in their entirety, which is why
    :py:func:`betty.hashid.hashid_file_meta` may be more suitable for large files.
    """
    return hashid(await read(file, mode="rb"))
