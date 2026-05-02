"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSET_DIRECTORY
from betty.plugins.asset_directory.maps import MAPS
from betty.plugins.asset_directory.trees import TREES

_ID = "raspberry-mint"
RASPBERRY_MINT: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _ID, assets=ASSET_DIRECTORY / _ID, before={MAPS, TREES}
)
