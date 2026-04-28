"""
Webpack assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

WEBPACK: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "webpack", assets=ASSETS_DIRECTORY / "webpack"
)
