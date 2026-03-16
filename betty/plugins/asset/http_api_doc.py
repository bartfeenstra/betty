"""
HTTP API Documentation assets.
"""

from __future__ import annotations

from typing import final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH


@final
@AssetDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    assets=ASSETS_DIRECTORY_PATH / "http-api-doc",
)
class HttpApiDoc(Asset):
    """
    .. plugin:: asset:http-api-doc.
    """
