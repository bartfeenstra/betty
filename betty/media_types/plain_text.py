from typing import Final  # noqa: D100

from betty.locale.localizable.gettext import _
from betty.media_type import MediaType, MediaTypeDefinition

PLAIN_TEXT: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "plain-text",
    label=_("Plain text"),
    media_type=MediaType("text/plain", extensions=[".txt"]),
)
"""
The media type for plain text content.
"""
