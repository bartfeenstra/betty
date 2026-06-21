from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

JSON_LD: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json-ld",
    label="JSON-LD",
    media_type=MediaType("application/ld+json", extensions=[".json"]),
)
"""
The media type for JSON-LD content.
"""
