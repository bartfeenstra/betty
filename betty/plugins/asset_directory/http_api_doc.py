"""
HTTP API Documentation assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY

HTTP_API_DOC: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "http-api-doc", assets=ASSETS_DIRECTORY / "http-api-doc"
)
