"""
Render plain text to HTML.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.html import plain_text_to_html
from betty.localizables.gettext import _
from betty.media_types import plain_text
from betty.render import Renderer, RendererDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaTypeDefinition


@RendererDefinition("plain-text", label=_("Plain text"))
class PlainText(Renderer):
    """
    .. plugin:: renderer:plain-text.
    """

    @override
    @property
    def media_type(self) -> MediaTypeDefinition:
        return plain_text

    @override
    async def render(self, content: str, /) -> str:
        return plain_text_to_html(content)
