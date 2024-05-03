"""
Provides utilities to generate unique IDs through hashing.

This module MUST NOT be used for security purposes.
"""

from hashlib import md5
from os.path import getmtime
from pathlib import Path

import aiofiles


def _hashid_bytes(key: bytes) -> str:
    return md5(key, usedforsecurity=False).hexdigest()


def hashid(key: bytes | str) -> str:
    """
    Create a hash ID for a key.
    """
    if isinstance(key, str):
        key = key.encode()
    return _hashid_bytes(key)


def hashid_sequence(*keys: bytes | str) -> str:
    """
    Create a hash ID from a sequence of keys.
    """
    return hashid(":".join(map(hashid, keys)))


async def hashid_file_meta(file_path: Path) -> str:
    """
    Create a hash ID for a file based on its metadata.

    This function relies on the file path and last modified time for uniqueness.
    File contents are ignored. This may be suitable for large files whose
    exact contents may not be very relevant in the context the ID is used in.
    """
    return hashid(f"{getmtime(file_path)}:{file_path}")


async def hashid_file_content(file_path: Path) -> str:
    """
    Create a hash ID for a file based on its contents.
    """
    async with aiofiles.open(file_path, "rb") as f:
        file_content = await f.read()
    return _hashid_bytes(file_content)
