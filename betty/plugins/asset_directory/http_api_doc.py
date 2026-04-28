"""
HTTP API Documentation assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDirectoryDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

HTTP_API_DOC: Final[AssetDirectoryDefinition] = AssetDirectoryDefinition(
    "http-api-doc", assets=ASSETS_DIRECTORY_PATH / "http-api-doc"
)
