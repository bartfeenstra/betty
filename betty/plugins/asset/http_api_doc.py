"""
HTTP API Documentation assets.
"""

from __future__ import annotations

from typing import Final

from betty.asset import AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH

HTTP_API_DOC: Final[AssetDefinition] = AssetDefinition(
    "http-api-doc", assets=ASSETS_DIRECTORY_PATH / "http-api-doc"
)
