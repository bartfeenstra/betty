"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import suppress
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, final

from aiofiles.os import makedirs
from typing_extensions import override

from betty.locale.localizable import _
from betty.media_type import UnsupportedMediaType, match_extension, match_media_type
from betty.plugin import ClassedPluginDefinition, ClassedPluginTypeDefinition
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.job import Context
    from betty.locale.localizer import Localizer
    from betty.media_type import MediaType


CopyFunction: TypeAlias = Callable[[Path, Path], Awaitable[None]]


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
        data: Mapping[str, Any] | None = None,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
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

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="renderer",
        label=_("Renderer"),
        cls=Renderer,
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
        data: Mapping[str, Any] | None = None,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> str:
        return await self._get_renderer(media_type).render(
            content,
            media_type,
            data=data,
            job_context=job_context,
            localizer=localizer,
        )


@internal
def make_copy_function(
    renderer: Renderer,
    *,
    data: Mapping[str, Any] | None = None,
    job_context: Context | None = None,
    localizer: Localizer | None = None,
    www_directory_path: Path | None = None,
    is_localized_and_multilingual: bool | None = None,
) -> CopyFunction:
    """
    Make a copy function for this renderer that renders supported files.
    """

    async def _copy_function(source_path: Path, destination_path: Path) -> None:
        nonlocal data
        await makedirs(destination_path.parent, exist_ok=True)
        try:
            media_type, extension = match_extension(source_path, renderer.media_types)
        except UnsupportedMediaType:
            copy2(source_path, destination_path)
            return

        destination_path = destination_path.with_name(
            destination_path.name[: -len(extension)]
        )

        if www_directory_path:
            try:
                relative_file_destination_path = destination_path.relative_to(
                    www_directory_path
                )
            except ValueError:
                pass
            else:
                resource_parts = relative_file_destination_path.parts
                if is_localized_and_multilingual:
                    resource_parts = resource_parts[1:]
                resource = "/".join(resource_parts)
                data = {} if data is None else dict(data)
                data["page_resource"] = f"betty:///{resource}"
        with open(source_path) as f:
            content = f.read()
        rendered_content = await renderer.render(
            content,
            media_type,
            data=data,
            job_context=job_context,
            localizer=localizer,
        )
        with open(destination_path, "w") as f:
            f.write(rendered_content)

    return _copy_function
