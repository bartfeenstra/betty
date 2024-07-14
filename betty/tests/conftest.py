"""
Integrate Betty with pytest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import filterwarnings

import pytest
from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import AsyncIterator


@pytest.fixture(autouse=True)
def _raise_deprecation_warnings_as_errors() -> None:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        "error",
        category=BettyDeprecationWarning,
    )


@pytest.fixture()
async def binary_file_cache(tmp_path: Path) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(tmp_path)


@pytest.fixture()
async def new_temporary_app() -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    async with App.new_temporary() as app, app:
        yield app
