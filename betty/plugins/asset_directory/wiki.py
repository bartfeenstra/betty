"""
Wiki assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

WIKI: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "wiki", assets=ASSETS_DIRECTORY / "wiki"
)
