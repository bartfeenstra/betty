"""
Provide media types.
"""

from __future__ import annotations

from betty.media_type import MediaType

#: The media type for HTML content.
HTML = MediaType("text/html")


#: The media type for JSON content.
JSON = MediaType("application/json")


#: The media type for JSON-LD content.
JSON_LD = MediaType("application/ld+json")


#: The media type for PDF documents.
PDF = MediaType("application/pdf")


#: The media type for plain text content.
PLAIN_TEXT = MediaType("text/plain")


#: The media type for SVG images.
SVG = MediaType("image/svg+xml")
