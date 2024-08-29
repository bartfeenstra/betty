"""
Common media types.
"""

from betty.media_type import MediaType

#: The media type for HTML content.
HTML = MediaType("text/html", file_extensions=[".html"])

#: The media type for HTML content as a Jinja2 template file.
JINJA2_HTML = MediaType("text/x.betty.jinja2-html", file_extensions=[".html.j2"])

#: The media type for JSON-LD content.
JSON_LD = MediaType("application/ld+json", file_extensions=[".json"])

#: The media type for plain text content.
PLAIN_TEXT = MediaType("text/plain", file_extensions=[".txt"])
