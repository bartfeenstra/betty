"""
Wiki assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH


@final
@AssetDefinition("wiki", label="Wiki", assets=ASSETS_DIRECTORY_PATH / "wiki")
class Wiki(Asset):
    """
    .. plugin:: asset:wiki.
    """
