"""
Maps assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH


@final
@AssetDefinition("maps", label="Maps", assets=ASSETS_DIRECTORY_PATH / "maps")
class Maps(Asset):
    """
    .. plugin:: asset:maps.
    """
