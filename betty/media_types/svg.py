from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

SVG: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "svg", label="SVG", media_type=MediaType("image/svg+xml", extensions=[".svg"])
)
"""
The media type for SVG images.
"""
