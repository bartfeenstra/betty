"""
Universe assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH


@final
@AssetDefinition(
    "universe",
    assets=ASSETS_DIRECTORY_PATH / "universe",
    after=lambda _: True,
    auto=True,
)
class Universe(Asset):
    """
    .. plugin:: asset:universe.
    """
