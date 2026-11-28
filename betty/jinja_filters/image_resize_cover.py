"""
The ``image_resize_cover`` Jinja filter.
"""

from __future__ import annotations

from asyncio import to_thread
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Self, final, override

from jinja2 import pass_context

from betty.content_types import png
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.factory import Manufacturable
from betty.hashid import hashid_file_meta
from betty.image.resize_cover import resize_cover
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.project import Project

if TYPE_CHECKING:
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
        self._file_directory = www_directory / "file"

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
        width, height = size
        file = filey if isinstance(filey, File) else filey.file
        assert file is not None
        file_reference = filey if isinstance(filey, FileReference) else None

        if (
            focus is None
            and file_reference is not None
            and file_reference.focus is not None
        ):
            focus = file_reference.focus

        job_context = context_document(context).context

        if width is None:
            key = f"-x{height}"
        elif height is None:
            key = f"{width}x-"
        else:
            key = f"{width}x{height}"
        if focus is not None:
            key += f"-{focus[0]}x{focus[1]}x{focus[2]}x{focus[3]}"

        cache_key = f"{await hashid_file_meta(file.path)}:{key}"
        execute_filter = True
        if job_context:
            async with job_context.store.with_scope(self.definition.id).hasset(
                cache_key
            ) as setter:
                if setter:
                    await setter(True)
                else:
                    execute_filter = False
        path_parts = (file.id, "file", self.definition.id, key + png.extension)
        if execute_filter:
            destination = Path(self._file_directory, *path_parts)
            # For monolingual sites, these paths overlap with those created by
            # :py:class:`betty.jobs.generate_entity.GenerateEntity`, but not for multilingual sites. We therefore try to
            # create all missing parents, but also allow the directory to exist already.
            await to_thread(destination.parent.mkdir, exist_ok=True, parents=True)
            cache_file = self._binary_file_cache.file(cache_key)
            if not cache_file.exists():
                image = resize_cover(
                    await self._imager.open(file.path), size, focus=focus
                )
                await to_thread(cache_file.parent.mkdir, exist_ok=True, parents=True)
                await self._imager.save(image, cache_file, content_type=png)
            copyfile(cache_file, destination)
        return f"betty-static:///file/{'/'.join(path_parts)}"
