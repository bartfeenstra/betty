from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

PDF: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "pdf", label="PDF", media_type=MediaType("application/pdf", extensions=[".pdf"])
)
"""
The media type for PDF documents.
"""
