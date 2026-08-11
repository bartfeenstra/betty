"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.html import plain_text_to_html
from betty.localizables.gettext import _, ngettext
from betty.media_type import resolve_media_type
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.media_type import MediaType, ResolvableMediaType
    from betty.requirement import Requires


class Renderer(Plugin["RendererDefinition"], metaclass=ABCMeta):
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
class RendererDefinition(HumanFacingDefinition, PluginClsDefinition[Renderer]):
    """
    .. plugin_type:: renderer.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        auto: bool = True,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            label=label,
            description=description,
            requires=requires,
        )


@final
class RenderDispatcher:
    """
    Dispatch content to a renderer that supports it.

    Unsupported content is rendered as plain text to make it safe for inclusion in HTML.
    """

    def __init__(self, *renderers: Renderer):
        self._renderers = {renderer.media_type: renderer for renderer in renderers}

    async def render(
        self, content: str, media_type: ResolvableMediaType | None, /
    ) -> str:
        """
        Render the content.
        """
        if media_type:
            media_type = resolve_media_type(media_type)
        else:
            return plain_text_to_html(content)
        try:
            renderer = self._renderers[media_type]
        except KeyError:
            return plain_text_to_html(content)
        else:
            return await renderer.render(content)
