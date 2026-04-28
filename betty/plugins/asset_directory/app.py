"""
App assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

APP: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "app", assets=ASSETS_DIRECTORY_PATH / "app", after=lambda _: True, auto=True
)
