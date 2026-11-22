"""
The ``image_resize_cover`` Jinja filter.
"""

from __future__ import annotations

from shutil import copyfile
from typing import TYPE_CHECKING, Self, final, override
from urllib.parse import quote

from jinja2 import pass_context

from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.factory import Manufacturable
from betty.hashid import hashid_file_meta
from betty.image.resize_cover import resize_cover
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.media_types import jpeg, svg
from betty.project import Project

if TYPE_CHECKING:
    from pathlib import Path

    from betty.image import Imager
    from betty.stores.file import TransientBinaryFileStore

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.image import FocusArea, Size


@final
@JinjaFilterDefinition("image-resize-cover", auto=True)
class ImageResizeCover(JinjaFilter, Manufacturable):
    """
    Preprocess an image file for use in a page.

    .. plugin:: jinja-filter:image-resize-cover
    """

    def __init__(
        self,
        *,
        binary_file_cache: TransientBinaryFileStore,
        imager: Imager,
        www_directory: Path,
    ):
        self._binary_file_cache = binary_file_cache
        self._imager = imager
        self._www_directory = www_directory

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            binary_file_cache=project.binary_file_cache.with_scope("image"),
            imager=await project.app.imager,
            www_directory=project.www_directory,
        )

    @pass_context
    async def __call__(
        self,
        context: Context,
        filey: File | FileReference,
        size: Size,
        /,
        *,
        focus: FocusArea | None = None,
    ) -> str:
        """
        :return: A ``betty-static://`` URL resource from which a public URL can be generated.
        """
        # @todo Check that the image type can be read
        file = filey if isinstance(filey, File) else filey.file
        assert file is not None
        file_reference = filey if isinstance(filey, FileReference) else None

        if (
            focus is None
            and file_reference is not None
            and file_reference.focus is not None
        ):
            focus = file_reference.focus

        # Treat SVGs as regular files.
        if file.media_type and file.media_type == svg:
            return f"betty-static:///file/{quote(file.id)}/file/{quote(file.name)}"

        job_context = context_document(context).context

        destination_name = f"{file.id}-"
        width, height = size
        if width is None:
            destination_name += f"-x{height}"
        elif height is None:
            destination_name += f"{width}x-"
        else:
            destination_name += f"{width}x{height}"
        if focus is not None:
            destination_name += f"-{focus[0]}x{focus[1]}x{focus[2]}x{focus[3]}.jpg"

        file_directory = self._www_directory / "file"

        job_store_key = f"{await hashid_file_meta(file.path)}:{destination_name}"
        execute_filter = True
        if job_context:
            async with job_context.store.with_scope("filter_image").hasset(
                job_store_key
            ) as setter:
                if setter:
                    await setter(True)
                else:
                    execute_filter = False
        if execute_filter:
            destination_file = file_directory / destination_name
            # @todo Do we need to call this all the time?
            file_directory.mkdir(exist_ok=True, parents=True)

            cache_file = self._binary_file_cache.file(job_store_key)
            if cache_file.exists():
                copyfile(cache_file, destination_file)
            else:
                image = resize_cover(
                    await self._imager.read(file.path), size, focus=focus
                )
                await self._imager.write(image, cache_file, media_type=jpeg)

        return f"betty-static:///file/{quote(destination_name)}"
