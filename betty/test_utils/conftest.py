"""
Betty/pytest test utilities.

Add ``from betty.test_utils.conftest import *`` to your project's ``conftest.py``
to start using these utilities.
"""

from __future__ import annotations


__all__ = [
    "binary_file_cache",
    "new_temporary_app",
]

from typing import TYPE_CHECKING

import pytest

from betty.app import App
from betty.cache.file import BinaryFileCache

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import AsyncIterator


@pytest.fixture
async def binary_file_cache(tmp_path: Path) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(tmp_path)


@pytest.fixture
async def new_temporary_app() -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    async with App.new_temporary() as app, app:
        yield app
