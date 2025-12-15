"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.html import plain_text_to_html
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


class Renderer(ABC, Plugin["RendererDefinition"]):
    """
    Render content in a different media type to HTML.

    Read more about :doc:`/development/plugin/renderer`.
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
    Renderer,
    _("Renderer"),
    _("Renderers"),
    ngettext("{count} renderer", "{count} renderers"),
    discovery=EntryPointDiscovery("betty.renderer"),
)
class RendererDefinition(HumanFacingPluginDefinition[Renderer]):
    """
    A renderer definition.

    Read more about :doc:`/development/plugin/renderer`.
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
