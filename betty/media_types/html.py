from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

HTML: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "html", label="HTML", media_type=MediaType("text/html", extensions=[".html"])
)
"""
The media type for HTML content.
"""
