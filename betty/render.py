"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.media_type import UnsupportedMediaType, match_media_type
from betty.plugin import (
    ClassedPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.media_type import MediaType
    from betty.resource import Context


class Renderer(ABC):
    """
    Render content.

    Read more about :doc:`/development/plugin/renderer`.
    """

    @property
    @abstractmethod
    def media_types(self) -> Sequence[MediaType]:
        """
        The media types this renderer can render from.
        """

    @abstractmethod
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        resource: Context | None = None,
    ) -> str:
        """
        Render content.
        """


@final
class RendererDefinition(ClassedPluginDefinition[Renderer]):
    """
    A renderer definition.

    Read more about :doc:`/development/plugin/renderer`.
    """

    plugin_type_cls = Renderer
    type = PluginTypeDefinition(
        id="renderer",
        label=_("Renderer"),
        discoveries=EntryPointDiscovery("betty.renderer"),
    )


@final
class ProxyRenderer(Renderer):
    """
    Render using a sequence of other renderers.
    """

    def __init__(self, upstreams: Sequence[Renderer]):
        self._upstreams = upstreams
        self._media_types = [
            media_type
            for renderer in self._upstreams
            for media_type in renderer.media_types
        ]

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return self._media_types

    def _get_renderer(self, media_type: MediaType) -> Renderer:
        for renderer in self._upstreams:
            with suppress(UnsupportedMediaType):
                match_media_type(media_type, renderer.media_types)
                return renderer
        raise UnsupportedMediaType(media_type)

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        resource: Context | None = None,
    ) -> str:
        return await self._get_renderer(media_type).render(
            content, media_type, resource=resource
        )
