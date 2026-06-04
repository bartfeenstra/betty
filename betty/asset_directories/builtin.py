"""
App assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import asset_directory

_id: Final[str] = "builtin"
builtin: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _id, assets=asset_directory / _id, after=lambda _: True, auto=True
)
