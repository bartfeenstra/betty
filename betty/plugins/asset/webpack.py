"""
Webpack assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

WEBPACK: Final[AssetDefinition] = AssetDefinition(
    "webpack", assets=ASSETS_DIRECTORY_PATH / "webpack"
)
