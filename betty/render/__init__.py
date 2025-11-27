"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.html import plain_text_to_html
from betty.locale.localizable import _
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    from betty.media_type import MediaType


class Renderer(Plugin, ABC):
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
class RendererPlugin(PluginDefinition[Renderer]):
    """
    A renderer definition.

    Read more about :doc:`/development/plugin/renderer`.
    """

    plugin_type_cls = Renderer
    type = PluginTypeDefinition(
        "renderer",
        _("Renderer"),
        discoveries=EntryPointDiscovery("betty.renderer"),
    )


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
