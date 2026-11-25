"""
Media type plugins.
"""

from __future__ import annotations

from typing import Final

from betty.localizables.gettext import _
from betty.media_type import MediaType, MediaTypeDefinition

html: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "html", label="HTML", media_type=MediaType("text/html", extensions=[".html"])
)
"""
The media type for HTML content.
"""

jinja: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jinja",
    label=_("Jinja template"),
    media_type=MediaType("text/x.betty.jinja2", extensions=[".j2"]),
)
"""
The media type for Jinja2 templates.
"""

json: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json", label="JSON", media_type=MediaType("application/json", extensions=[".json"])
)
"""
The media type for JSON content.
"""

pdf: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "pdf", label="PDF", media_type=MediaType("application/pdf", extensions=[".pdf"])
)
"""
The media type for PDF documents.
"""

plain_text: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "plain-text",
    label=_("Plain text"),
    media_type=MediaType("text/plain", extensions=[".txt"]),
)
"""
The media type for plain text content.
"""

svg: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "svg", label="SVG", media_type=MediaType("image/svg+xml", extensions=[".svg"])
)
"""
The media type for SVG images.
"""

yaml: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "yaml",
    label="YAML",
    media_type=MediaType("application/yaml", extensions=[".yaml", ".yml"]),
)
"""
The media type for YAML content.
"""
