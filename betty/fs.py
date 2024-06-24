"""
Provide file system utilities.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterable

from betty import _ROOT_DIRECTORY_PATH


ROOT_DIRECTORY_PATH = _ROOT_DIRECTORY_PATH


ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "assets"


PREBUILT_ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "prebuild"


HOME_DIRECTORY_PATH = Path.home() / ".betty"


async def iterfiles(path: Path) -> AsyncIterable[Path]:
    """
    Recursively iterate over any files found in a directory.
    """
    for dir_path, _, filenames in os.walk(str(path)):
        for filename in filenames:
            yield Path(dir_path) / filename
