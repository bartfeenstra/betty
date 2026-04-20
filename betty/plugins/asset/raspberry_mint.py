"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.plugins.asset.maps import MAPS
from betty.plugins.asset.trees import TREES

RASPBERRY_MINT: Final[AssetDefinition] = AssetDefinition(
    "raspberry-mint",
    assets=ASSETS_DIRECTORY_PATH / "raspberry-mint",
    before={MAPS, TREES},
)
