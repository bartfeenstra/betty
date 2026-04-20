"""
Trees assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

TREES: Final[AssetDefinition] = AssetDefinition(
    "trees", assets=ASSETS_DIRECTORY_PATH / "trees"
)
