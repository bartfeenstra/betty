"""
Webpack assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

WEBPACK: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "webpack", assets=ASSETS_DIRECTORY_PATH / "webpack"
)
