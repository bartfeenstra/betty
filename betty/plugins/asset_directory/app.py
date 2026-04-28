"""
App assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

APP: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "app", assets=ASSETS_DIRECTORY / "app", after=lambda _: True, auto=True
)
