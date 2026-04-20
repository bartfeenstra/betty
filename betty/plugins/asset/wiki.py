"""
Wiki assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

WIKI: Final[AssetDefinition] = AssetDefinition(
    "wiki", assets=ASSETS_DIRECTORY_PATH / "wiki"
)
