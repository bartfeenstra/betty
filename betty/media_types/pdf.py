from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

PDF: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "pdf", label="PDF", media_type=MediaType("application/pdf", extensions=[".pdf"])
)
"""
The media type for PDF documents.
"""
