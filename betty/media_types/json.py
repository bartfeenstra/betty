from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

JSON: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json", label="JSON", media_type=MediaType("application/json", extensions=[".json"])
)
"""
The media type for JSON content.
"""
