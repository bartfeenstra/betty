"""
Maps assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

MAPS: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "maps", assets=ASSETS_DIRECTORY_PATH / "maps"
)
