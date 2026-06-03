from typing import Final  # noqa: D100

from betty.locale.localizable.gettext import _
from betty.media_type import MediaType, MediaTypeDefinition

JINJA: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jinja",
    label=_("Jinja template"),
    media_type=MediaType("text/x.betty.jinja2", extensions=[".j2"]),
)
"""
The media type for Jinja2 template files.
"""
