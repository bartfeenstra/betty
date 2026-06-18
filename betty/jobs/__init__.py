"""
Job implementations.
"""

from __future__ import annotations

from asyncio import to_thread
from typing import TYPE_CHECKING

from betty.file import write

if TYPE_CHECKING:
    from pathlib import Path


async def _create_resource(file: Path, content: str, /) -> None:
    await to_thread(file.parent.mkdir, exist_ok=True, parents=True)
    return await write(file, content)


async def _create_html_resource(resource: Path, content: str, /) -> None:
    await _create_resource(resource / "index.html", content)


async def _create_json_resource(resource: Path, content: str, /) -> None:
    await _create_resource(resource / "index.json", content)
