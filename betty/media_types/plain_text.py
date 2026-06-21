from __future__ import annotations  # noqa: D100

from typing import Final

from betty.localizables.gettext import _
from betty.media_type import MediaType, MediaTypeDefinition

PLAIN_TEXT: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "plain-text",
    label=_("Plain text"),
    media_type=MediaType("text/plain", extensions=[".txt"]),
)
"""
The media type for plain text content.
"""
