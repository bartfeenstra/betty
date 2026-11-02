"""
Asset plugins.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import asset_directory

builtin: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "builtin", assets=asset_directory / "builtin", after=lambda _: True, auto=True
)
maps: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "maps", assets=asset_directory / "maps"
)
trees: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "trees", assets=asset_directory / "trees"
)
raspberry_mint: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "raspberry-mint", assets=asset_directory / "raspberry-mint", before={maps, trees}
)
webpack: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "webpack", assets=asset_directory / "webpack"
)
wiki: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "wiki", assets=asset_directory / "wiki"
)
