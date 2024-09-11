"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final, TYPE_CHECKING

import aiofiles
from typing_extensions import override

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType, UnsupportedMediaType, MediaTypeIndicator
from betty.os import CopyFunction, DEFAULT_COPY_FUNCTION
from betty.plugin import Plugin
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.typing import internal
from pathlib import Path

if TYPE_CHECKING:
    from betty.plugin import PluginRepository
    from betty.locale.localizer import Localizer
    from betty.job import Context
    from collections.abc import Sequence, Mapping


class Renderer(ABC):
    """
    Render content to HTML.

    See also :py:class:`betty.render.RendererPlugin`.
    """

    def to_media_type(
        self, media_type_indicator: MediaTypeIndicator
    ) -> tuple[MediaType, MediaType] | None:
        """
        Get the media type the given media typey can be rendered to, if available.
        """
        if isinstance(media_type_indicator, Path):
            media_type_indicator = media_type_indicator.name
        if isinstance(media_type_indicator, str):
            for from_media_type, to_media_type in self.media_types.items():
                for file_extension in from_media_type.file_extensions:
                    if media_type_indicator.endswith(file_extension):
                        return MediaType(
                            str(from_media_type),
                            file_extensions=[
                                file_extension,
                                *[
                                    from_file_extension
                                    for from_file_extension in from_media_type.file_extensions
                                    if from_file_extension != file_extension
                                ],
                            ],
                        ), to_media_type
        else:
            for from_media_type, to_media_type in self.media_types.items():
                if (
                    media_type_indicator.type == from_media_type.type
                    and media_type_indicator.subtype == from_media_type.subtype
                    and media_type_indicator.suffix == from_media_type.suffix
                ):
                    return from_media_type, to_media_type
        return None

    def assert_to_media_type(
        self, media_type_indicator: MediaTypeIndicator
    ) -> tuple[MediaType, MediaType]:
        """
        Get the media type the given media typey can be rendered to.
        """
        media_type = self.to_media_type(media_type_indicator)
        if media_type is None:
            raise RuntimeError(f'{self} cannot render "{media_type_indicator}"')
        return media_type

    @property
    @abstractmethod
    def media_types(self) -> Mapping[MediaType, MediaType]:
        """
        The media types this renderer can render.

        :return: Keys are media types of content this renderer can render, and values are the media types of the
            content after rendering.
        """
        pass

    @abstractmethod
    async def render(
        self,
        content: str,
        media_type_indicator: MediaTypeIndicator,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> tuple[str, MediaType, MediaType]:
        """
        Render content.

        :return: A 3-tuple:
            - The rendered content
            - The 'from' media type, which is the content's original media type determined by the renderer.
                This media type may differ from the media type indicator, e.g. to be more generic.
                If the media type indicator is a file name, the returned media type's preferred file extension
                MUST be the file name's suffix.
            - The 'to' media type, which is the media type of the rendered content.
        """
        pass

    def copy_function(
        self,
        *,
        copy_function: CopyFunction = DEFAULT_COPY_FUNCTION,
        job_context: Context | None = None,
        localizer: Localizer = DEFAULT_LOCALIZER,
    ) -> CopyFunction:
        """
        Create a :py:type:`betty.os.CopyFunction` for this renderer that renders supported files.
        """

        async def _copy_function(source_path: Path, destination_path: Path) -> Path:
            if self.to_media_type(source_path.name):
                async with aiofiles.open(source_path) as f:
                    content = await f.read()
                rendered_content, from_media_type, to_media_type = await self.render(
                    content,
                    source_path.name,
                    job_context=job_context,
                    localizer=localizer,
                )

                destination_path = destination_path.parent / (
                    destination_path.name[
                        : -len(from_media_type.preferred_file_extension or "")
                    ]
                    + to_media_type.preferred_file_extension
                    or ""
                )

                async with aiofiles.open(destination_path, "w") as f:
                    await f.write(rendered_content)
            return await copy_function(source_path, destination_path)

        return _copy_function


class RendererPlugin(Renderer, Plugin):
    """
    A renderer as a plugin.

    Read more about :doc:`/development/plugin/renderer`.
    """

    pass


RENDERER_REPOSITORY: PluginRepository[RendererPlugin] = EntryPointPluginRepository(
    "betty.renderer"
)
"""
The renderer plugin repository.

Read more about :doc:`/development/plugin/renderer`.
"""


@internal
@final
class ProxyRenderer(Renderer):
    """
    Render content using the first available upstream renderer.
    """

    def __init__(self, renderers: Sequence[Renderer]):
        self._renderers = renderers
        self._media_types = {
            from_media_type: to_media_type
            for renderer in self._renderers
            for from_media_type, to_media_type in renderer.media_types.items()
        }

    @override
    @property
    def media_types(self) -> Mapping[MediaType, MediaType]:
        return self._media_types

    @override
    async def render(
        self,
        content: str,
        media_type_indicator: MediaTypeIndicator,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> tuple[str, MediaType, MediaType]:
        for renderer in self._renderers:
            if renderer.to_media_type(media_type_indicator):
                return await renderer.render(
                    content,
                    media_type_indicator,
                    job_context=job_context,
                    localizer=localizer,
                )
        raise UnsupportedMediaType()
