"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.plugins.asset_directory.maps import MAPS
from betty.plugins.asset_directory.trees import TREES

RASPBERRY_MINT: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "raspberry-mint",
    assets=ASSETS_DIRECTORY_PATH / "raspberry-mint",
    before={MAPS, TREES},
)
