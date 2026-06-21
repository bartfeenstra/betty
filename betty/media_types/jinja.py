from __future__ import annotations  # noqa: D100

from typing import Final

from betty.localizables.gettext import _
from betty.media_type import MediaType, MediaTypeDefinition

JINJA: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jinja",
    label=_("Jinja template"),
    media_type=MediaType("text/x.betty.jinja2", extensions=[".j2"]),
)
"""
The media type for Jinja2 template files.
"""
