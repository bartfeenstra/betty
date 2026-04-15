"""
File operations.
"""

from __future__ import annotations

from asyncio import to_thread
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from pathlib import Path

    from _typeshed import (
        OpenBinaryModeReading,
        OpenBinaryModeWriting,
        OpenTextModeReading,
        OpenTextModeWriting,
    )


def _read(
    file: Path,
    *,
    encoding: str | None,
    mode: OpenTextModeReading | OpenBinaryModeReading,
) -> str | bytes:
    with open(file, encoding=encoding, mode=mode) as f:
        return f.read()


@overload
async def read(
    file: Path, *, encoding: str = "utf-8", mode: OpenTextModeReading = "r"
) -> str:
    pass


@overload
async def read(
    file: Path, *, encoding: None = None, mode: OpenBinaryModeReading
) -> bytes:
    pass


async def read(file, *, encoding=None, mode="r"):
    """
    Read content from a file.
    """
    if "b" not in mode and encoding is None:
        # Mimic Python 3.15.
        encoding = "utf-8"
    return await to_thread(_read, file, encoding=encoding, mode=mode)


def _write(
    file: Path,
    content: str | bytes,
    *,
    encoding: str | None,
    mode: OpenTextModeWriting | OpenBinaryModeWriting,
) -> None:
    with open(file, encoding=encoding, mode=mode) as f:
        f.write(content)


@overload
async def write(
    file: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: OpenTextModeWriting = "w",
) -> None:
    pass


@overload
async def write(
    file: Path, content: bytes, *, encoding: None = None, mode: OpenBinaryModeWriting
) -> None:
    pass


async def write(file, content, *, encoding=None, mode="w") -> None:
    """
    Write content to a file.
    """
    await to_thread(_write, file, content, encoding=encoding, mode=mode)
