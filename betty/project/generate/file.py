"""
File utilities for site generation.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncContextManager, TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper
    from collections.abc import AsyncIterator
    from pathlib import Path


@asynccontextmanager
async def create_file(path: Path) -> AsyncIterator[AsyncTextIOWrapper]:
    """
    Create the file for a resource.
    """
    await makedirs(path.parent, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        yield f


def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for an HTML resource.
    """
    return create_file(path / "index.html")


def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for a JSON resource.
    """
    return create_file(path / "index.json")
