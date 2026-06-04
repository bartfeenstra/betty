"""
HTTP API Documentation assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import asset_directory

_id: Final[str] = "http-api-doc"
http_api_doc: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    _id, assets=asset_directory / _id
)
