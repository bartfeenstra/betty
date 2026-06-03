"""
App assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSET_DIRECTORY

_ID = "builtin"
BUILTIN: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _ID, assets=ASSET_DIRECTORY / _ID, after=lambda _: True, auto=True
)
