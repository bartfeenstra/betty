"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.asset_directories.maps import maps
from betty.asset_directories.trees import trees
from betty.dirs import asset_directory

_id: Final[str] = "raspberry-mint"
raspberry_mint: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _id, assets=asset_directory / _id, before={maps, trees}
)
