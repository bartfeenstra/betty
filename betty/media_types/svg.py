from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

SVG: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "svg", label="SVG", media_type=MediaType("image/svg+xml", extensions=[".svg"])
)
"""
The media type for SVG images.
"""
