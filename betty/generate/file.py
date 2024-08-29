"""
File utilities for site generation.
"""

from __future__ import annotations

from typing import AsyncContextManager, cast, TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs
from aiofiles.threadpool.text import AsyncTextIOWrapper

if TYPE_CHECKING:
    from pathlib import Path


async def create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for a resource.
    """
    await makedirs(path.parent, exist_ok=True)
    return cast(
        AsyncContextManager[AsyncTextIOWrapper],
        aiofiles.open(path, "w", encoding="utf-8"),
    )


async def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for an HTML resource.
    """
    return await create_file(path / "index.html")


async def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for a JSON resource.
    """
    return await create_file(path / "index.json")
