"""
Maps assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

MAPS: Final[AssetDefinition] = AssetDefinition(
    "maps", assets=ASSETS_DIRECTORY_PATH / "maps"
)
