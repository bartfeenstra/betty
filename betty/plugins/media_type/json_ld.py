from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

JSON_LD: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json-ld",
    label="JSON-LD",
    media_type=MediaType("application/ld+json", extensions=[".json"]),
)
"""
The media type for JSON-LD content.
"""
