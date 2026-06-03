"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.asset_directories.maps import MAPS
from betty.asset_directories.trees import TREES
from betty.dirs import ASSET_DIRECTORY

_ID = "raspberry-mint"
RASPBERRY_MINT: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _ID, assets=ASSET_DIRECTORY / _ID, before={MAPS, TREES}
)
