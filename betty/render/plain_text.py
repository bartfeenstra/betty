"""
Render plain text to HTML.
"""

from typing_extensions import override

from betty.html import plain_text_to_html
from betty.locale.localizable.gettext import _
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.render import Renderer, RendererDefinition


@RendererDefinition("plain-text", label=_("Plain text"))
class PlainText(Renderer):
    """
    Render plain text to HTML.
    """

    @override
    @property
    def media_type(self) -> MediaType:
        return PLAIN_TEXT

    @override
    async def render(self, content: str, /) -> str:
        return plain_text_to_html(content)
