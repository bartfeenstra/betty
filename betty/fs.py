"""
Provide file system utilities.
"""

from __future__ import annotations

from pathlib import Path

from betty import _ROOT_DIRECTORY_PATH

ROOT_DIRECTORY_PATH = _ROOT_DIRECTORY_PATH


ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "assets"


DATA_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "data"


HOME_DIRECTORY_PATH = Path.home() / ".betty"
