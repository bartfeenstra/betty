from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

JSON: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json", label="JSON", media_type=MediaType("application/json", extensions=[".json"])
)
"""
The media type for JSON content.
"""
