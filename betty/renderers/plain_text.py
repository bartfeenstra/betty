"""
Render plain text to HTML.
"""

from __future__ import annotations

from typing import override

from betty.content_types import plain_text
from betty.html import plain_text_to_html
from betty.localizables.gettext import _
from betty.render import Renderer, RendererDefinition


@RendererDefinition("plain-text", label=_("Plain text"), media_types=plain_text)
class PlainText(Renderer):
    """
    .. plugin:: renderer:plain-text.
    """

    @override
    async def render(self, content: str, /) -> str:
        return plain_text_to_html(content)
