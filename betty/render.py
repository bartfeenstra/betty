"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, final

from aiofiles.os import makedirs
from typing_extensions import override

from betty.locale.localizable import _
from betty.media_type import UnsupportedMediaType, match_extension
from betty.plugin import ClassedPluginDefinition, ClassedPluginTypeDefinition
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.job import Context
    from betty.locale.localizer import Localizer
    from betty.media_type import MediaType


CopyFunction: TypeAlias = Callable[[Path, Path], Awaitable[None]]




class Renderer(ABC):
    """
    Render content.

    Read more about :doc:`/development/plugin/renderer`.
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
    @property
    @abstractmethod
    def input(self) -> MediaType:
        """
        The media type this renderer can render from.
        """

    @property
    @abstractmethod
    def output(self) -> MediaType:
        """
        The media type this renderer can render to.
        """


# @todo We need to thoroughly think through what we want and not conflate two different things:
# @todo 1. Converting one media type to another (e.g. Markdown to HTML)
# @todo 2. Templating languages (e.g. Jinja2 where the contained media type is the same as the output media type)
# @todo 3. Postprocessing, such as URL generation or HTML fixing.
# @todo
# @todo We can do 1 easily because we know the source content media type, and input and output media types of any renderers.
# @todo
# @todo We can do 2 easily as well, really, and 3 too....
# @todo
# @todo The problem lies in how we want to get from input to output.
# @todo We may not want to chain type 1 renderers (compound problems, graph resolution, ...)
# @todo We can easily chain type 2 renderers.
# @todo We can easily chain type 3 renderers.
# @todo
# @todo Type 1 is really the only conversion. Type 2 just resolves templating and leaves the rest intact.
# @todo Type 3 may cause conflicts but that depends on whether individual renderers act on the same content.
# @todo
# @todo
# @todo
# @todo
# @todo
# @todo
# @todo
# @todo
# @todo
# @todo
@final
class RendererChain(Renderer):
    """
    A chain of renderers.
    """

    def __init__(self, *renderers: tuple[Renderer,MediaType,MediaType]):
        self._renderers = renderers

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
        return await self._render(
            content,
            media_type,
            media_type,
            data=data,
            job_context=job_context,
            localizer=localizer,
        )

    async def _render(
        self,
        content: str,
        root_media_type: MediaType,
        media_type: MediaType,
        *,
        data: Mapping[str, Any] | None = None,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> str:
        # @todo How do we allow recursion but also let the caller know if there were any changes made to the content at all?
        # @todo Act
        # @todo
        # @todo
        for renderer,renderer_input, renderer_output in self._renderers:
            if media_type == renderer.input:
                return await self.render(
                    await renderer.render(
                        content,
                        media_type,
                        data=data,
                        job_context=job_context,
                        localizer=localizer,
                    ),
                    renderer.output,
                    data=data,
                    job_context=job_context,
                    localizer=localizer,
                )
        if media_type == root_media_type:
            raise UnsupportedMediaType.new(root_media_type)
        return content




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
            media_type, extension = match_extension(source_path, renderer.input)
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
