"""
Provide media types.
"""

from __future__ import annotations

from betty.media_type import MediaType

HTML = MediaType("text/html", extensions=[".html"])
"""
The media type for HTML content.
"""

JINJA2 = MediaType("text/x.betty.jinja2", extensions=[".j2"])
"""
The media type for Jinja2 template files.
"""

JSON = MediaType("application/json", extensions=[".json"])
"""
The media type for JSON content.
"""

JSON_LD = MediaType("application/ld+json", extensions=[".json"])
"""
The media type for JSON-LD content.
"""

PDF = MediaType("application/pdf", extensions=[".pdf"])
"""
The media type for PDF documents.
"""

PLAIN_TEXT = MediaType("text/plain", extensions=[".txt"])
"""
The media type for plain text content.
"""

SVG = MediaType("image/svg+xml", extensions=[".svg"])
"""
The media type for SVG images.
"""

YAML = MediaType("application/yaml", extensions=[".yaml", ".yml"])
"""
The media type for YAML content.
"""
