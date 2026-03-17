"""
Trees assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH


@final
@AssetDefinition("trees", assets=ASSETS_DIRECTORY_PATH / "trees")
class Trees(Asset):
    """
    .. plugin:: asset:trees.
    """
