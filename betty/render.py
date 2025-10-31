"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
)
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.job import Context
    from betty.locale.localizer import Localizer
    from betty.media_type import MediaType


class Renderer(ABC):
    """
    Render content to HTML.

    Read more about :doc:`/development/plugin/renderer`.
    """

    @property
    @abstractmethod
    def media_types(self) -> Sequence[MediaType]:
        """
        The media types this renderer can render.
        """

    @abstractmethod
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        """
        Render a single file.

        :return: The file's new path, which may have been changed, e.g. a
            renderer-specific extension may have been stripped from the end.
        """


@final
class RendererDefinition(ClassedPluginDefinition[Renderer]):
    """
    A renderer definition.

    Read more about :doc:`/development/plugin/renderer`.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="renderer",
        label=_("Renderer"),
        cls=Renderer,
    )


@internal
@final
class SequentialRenderer(Renderer):
    """
    Render using a sequence of other renderers.
    """

    def __init__(self, renderers: Sequence[Renderer]):
        self._renderers = renderers
        self._media_types = [
            media_type
            for renderer in self._renderers
            for media_type in renderer.media_types
        ]

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return self._media_types

    @override
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        for renderer in self._renderers:
            for renderer_media_type in renderer.media_types:
                for extension in renderer_media_type.extensions:
                    if str(file_path).endswith(extension):
                        return await renderer.render_file(
                            file_path,
                            job_context=job_context,
                            localizer=localizer,
                        )
        return file_path
