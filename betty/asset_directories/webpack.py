"""
Webpack assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import asset_directory

_id: Final[str] = "webpack"
webpack: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _id, assets=asset_directory / _id
)
