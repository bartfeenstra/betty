"""
Universe assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

UNIVERSE: Final[AssetDefinition] = AssetDefinition(
    "universe",
    assets=ASSETS_DIRECTORY_PATH / "universe",
    after=lambda _: True,
    auto=True,
)
