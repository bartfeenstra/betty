"""
Raspberry Mint assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.plugins.asset.maps import Maps
from betty.plugins.asset.trees import Trees


@final
@AssetDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    assets=ASSETS_DIRECTORY_PATH / "raspberry-mint",
    before={Maps, Trees},
)
class RaspberryMint(Asset):
    """
    .. plugin:: asset:raspberry-mint.
    """
