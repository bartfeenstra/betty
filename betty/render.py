"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final

from betty.content_type import ContentTypeDefinition
from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.html import plain_text_to_html
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class Renderer(HasDefinition["RendererDefinition"], metaclass=ABCMeta):
    """
    Render content in a different media type to HTML.
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
class RendererDefinition(
    HumanFacingDefinition, ClsDefinition[Renderer], PluginDefinition
):
    """
    .. plugin_type:: renderer.
    """

    def __init__(
        self,
        renderer_id: ResolvableMachineName,
        /,
        *,
        label: AnyLocalizable,
        media_types: ContentTypeDefinition | Iterable[ContentTypeDefinition],
        auto: bool = True,
        description: AnyLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            renderer_id,
            auto=auto,
            label=label,
            description=description,
            requires=requires,
        )
        self.media_types: Final[Sequence[ContentTypeDefinition]] = (
            (media_types,)
            if isinstance(media_types, ContentTypeDefinition)
            else tuple(media_types)
        )


@final
class RenderDispatcher:
    """
    Dispatch content to a renderer that supports it.

    Unsupported content is rendered as plain text to make it safe for inclusion in HTML.
    """

    def __init__(self, *renderers: Renderer):
        self._renderers = {
            media_type: renderer
            for renderer in renderers
            for media_type in renderer.definition.media_types
        }

    async def render(self, content: str, media_type: ContentTypeDefinition, /) -> str:
        """
        Render the content.
        """
        try:
            renderer = self._renderers[media_type]
        except KeyError:
            return plain_text_to_html(content)
        else:
            return await renderer.render(content)
