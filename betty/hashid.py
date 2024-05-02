"""
Provides utilities to generate unique IDs through hashing.

This module MUST NOT be used for security purposes.
"""

from hashlib import md5
from os.path import getmtime
from pathlib import Path

import aiofiles

_hasher = md5


def hashid(content: bytes | str) -> str:
    """
    Create an ID.
    """
    if isinstance(content, str):
        content = content.encode()
    return _hasher(content).hexdigest()


async def hashid_file_meta(path: Path) -> str:
    """
    Create an ID for a file based on its metadata.

    This function relies on the file path and last modified time for uniqueness.
    File contents are ignored. This may be suitable for large files whose
    exact contents may not be very relevant in the context the ID is used in.
    """
    return hashid(f"{getmtime(path)}:{path}")


async def hashid_file_content(path: Path) -> str:
    """
    Create an ID for a file based on its contents.
    """
    async with aiofiles.open(path, "rb") as f:
        content = await f.read()
    return hashid(content)
