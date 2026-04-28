"""
Maps assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

MAPS: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "maps", assets=ASSETS_DIRECTORY / "maps"
)
