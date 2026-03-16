"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.html import plain_text_to_html
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


class Renderer(ABC, Plugin["RendererDefinition"]):
    """
    Render content in a different media type to HTML.
    """

    @property
    @abstractmethod
    def media_type(self) -> MediaType:
        """
        The media type this renderer can render from.
        """

    @abstractmethod
    async def render(self, content: str, /) -> str:
        """
        Render content.
        """


@final
@PluginTypeDefinition(
    "renderer",
    label=_("Renderer"),
    label_plural=_("Renderers"),
    label_countable=ngettext("{count} renderer", "{count} renderers"),
)
class RendererDefinition(HumanFacingDefinition, PluginDefinition[Renderer]):
    """
    .. plugin_type:: renderer.
    """


@final
class RenderDispatcher:
    """
    Dispatch content to a renderer that supports it.

    Unsupported content is rendered as plain text to make it safe for inclusion in HTML.
    """

    def __init__(self, *renderers: Renderer):
        self._renderers = {renderer.media_type: renderer for renderer in renderers}

    async def render(self, content: str, media_type: MediaType, /) -> str:
        """
        Render the content.
        """
        try:
            renderer = self._renderers[media_type]
        except KeyError:
            return plain_text_to_html(content)
        else:
            return await renderer.render(content)
