"""
Maps assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSET_DIRECTORY

_ID = "maps"
MAPS: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _ID, assets=ASSET_DIRECTORY / _ID
)
