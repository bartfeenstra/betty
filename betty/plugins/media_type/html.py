from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

HTML: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "html", label="HTML", media_type=MediaType("text/html", extensions=[".html"])
)
"""
The media type for HTML content.
"""
