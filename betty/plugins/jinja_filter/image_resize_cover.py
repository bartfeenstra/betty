"""
The ``image_resize_cover`` Jinja filter.
"""

from __future__ import annotations

import warnings
from _asyncio import get_running_loop
from io import BytesIO
from typing import TYPE_CHECKING, Self, final, override
from urllib.parse import quote

from jinja2 import pass_context
from pdf2image.pdf2image import convert_from_path
from PIL import Image
from PIL.Image import DecompressionBombWarning

from betty.factory import Manufacturable
from betty.hashid import hashid_file_meta
from betty.image import image_file_path_format, resize_cover
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.os import _link_or_copy
from betty.plugins.entity.file import File
from betty.plugins.entity.file_reference import FileReference
from betty.plugins.jinja_filter.file import File as FileFilter
from betty.plugins.media_type.svg import SVG
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
    )
    from concurrent.futures import ProcessPoolExecutor
    from pathlib import Path

    from betty.cache.file import BinaryFileCache

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.image import FocusArea, Size


@final
@JinjaFilterDefinition(
    "image-resize-cover",
    requires={Project.jinja_filters.require(FileFilter)},
    auto=True,
)
class ImageResizeCover(JinjaFilter, Manufacturable):
    """
    Preprocess an image file for use in a page.

    .. plugin:: jinja-filter:image-resize-cover
    """

    def __init__(
        self,
        *,
        binary_file_cache: BinaryFileCache,
        file_filter: FileFilter,
        process_pool: ProcessPoolExecutor,
        www_directory: Path,
    ):
        self._binary_file_cache = binary_file_cache
        self._file_filter = file_filter
        self._process_pool = process_pool
        self._www_directory = www_directory

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            binary_file_cache=project.binary_file_cache.with_scope("image"),
            file_filter=await project.factory.new(FileFilter),
            process_pool=project.upstream.process_pool,
            www_directory=project.www_directory,
        )

    @pass_context
    async def __call__(
        self,
        context: Context,
        filey: File | FileReference,
        size: Size | None = None,
        *,
        focus: FocusArea | None = None,
    ) -> str:
        """
        :return: A ``betty-static://`` URL resource from which a public URL can be generated.
        """
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
        if file.media_type and file.media_type == SVG:
            return await self._file_filter(context, file)

        job_context = context_document(context).context

        destination_name = f"{file.id}-"
        if size is not None:
            width, height = size
            if width is None:
                destination_name += f"-x{height}"
            elif height is None:
                destination_name += f"{width}x-"
            else:
                destination_name += f"{width}x{height}"
        if focus is not None:
            destination_name += f"-{focus[0]}x{focus[1]}x{focus[2]}x{focus[3]}"

        file_directory_path = self._www_directory / "file"

        if file.media_type:
            if file.media_type.type == "image":
                image_loader = _load_image_image
                destination_name += file.path.suffix
            elif (
                file.media_type.type == "application"
                and file.media_type.subtype == "pdf"
            ):
                image_loader = _load_image_application_pdf
                destination_name += "." + "jpg"
            else:
                raise ValueError(
                    f'Cannot convert a file of media type "{file.media_type}" to an image.'
                )
        else:
            raise ValueError("Cannot convert a file without a media type to an image.")

        cache_item_id = f"{await hashid_file_meta(file.path)}:{destination_name}"
        execute_filter = True
        if job_context:
            async with job_context.cache.with_scope("filter_image").hasset(
                cache_item_id
            ) as setter:
                if setter:
                    await setter(True)
                else:
                    execute_filter = False
        if execute_filter:
            loop = get_running_loop()
            await loop.run_in_executor(
                self._process_pool,
                _execute_filter_image,
                image_loader,
                file.path,
                self._binary_file_cache.cache_item_file_path(cache_item_id),
                file_directory_path,
                destination_name,
                size,
                focus,
            )
        return f"betty-static:///file/{quote(destination_name)}"


def _load_image_image(file_path: Path) -> Image.Image:
    with open(file_path, "rb") as f:
        image_f = BytesIO(f.read())
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        return Image.open(image_f, formats=[image_file_path_format(file_path)])


def _load_image_application_pdf(file_path: Path) -> Image.Image:
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        return convert_from_path(file_path)[0]


def _execute_filter_image(
    image_loader: Callable[[Path], Image.Image],
    file_path: Path,
    cache_item_file_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    size: Size | None,
    focus: FocusArea | None,
) -> None:
    destination_file_path = destination_directory_path / destination_name
    destination_directory_path.mkdir(exist_ok=True, parents=True)

    # If no customizations are needed, work straight from the source.
    if size is None and file_path.suffix == destination_file_path.suffix:
        _link_or_copy(file_path, destination_file_path)
        return

    try:
        # Try using a previously cached image.
        _link_or_copy(cache_item_file_path, destination_file_path)
    except FileNotFoundError:
        # Apply customizations, and cache the customized image.
        original_image = converted_image = image_loader(file_path)
        try:
            cache_item_file_path.parent.mkdir(exist_ok=True, parents=True)
            if size is not None:
                converted_image = resize_cover(converted_image, size, focus=focus)
            converted_image.save(
                cache_item_file_path,
                format=image_file_path_format(destination_file_path),
            )
            del converted_image
        finally:
            original_image.close()
            del original_image
        _link_or_copy(cache_item_file_path, destination_file_path)
