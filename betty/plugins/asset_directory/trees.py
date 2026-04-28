"""
Trees assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

TREES: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "trees", assets=ASSETS_DIRECTORY / "trees"
)
