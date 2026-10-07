"""
The ``file`` Jinja filter.
"""

from __future__ import annotations

from asyncio import to_thread
from shutil import copyfile
from typing import TYPE_CHECKING, Self, final, override
from urllib.parse import quote

from jinja2 import pass_context

from betty.factory import Manufacturable
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.project import Project

if TYPE_CHECKING:
    from pathlib import Path

    from jinja2.runtime import Context

    from betty.entities.file import File as FileEntity


@final
@JinjaFilterDefinition("file", auto=True)
class File(JinjaFilter, Manufacturable):
    """
    Preprocess a file for use in a page.

    .. plugin:: jinja-filter:file
    """

    def __init__(self, *, www_directory: Path):
        self._www_directory = www_directory

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(www_directory=project.www_directory)

    @pass_context
    async def __call__(self, context: Context, file: FileEntity, /) -> str:
        """
        :return: A ``betty-static://`` URL resource from which a public URL can be generated.
        """
        job_context = context_document(context).context

        execute_filter = True
        if job_context:
            async with job_context.store.hasset(f"filter_file:{file.id}") as setter:
                if setter:
                    await setter(True)
                else:
                    execute_filter = False
        if execute_filter:
            file_destination_path = (
                self._www_directory / "file" / file.id / "file" / file.name
            )
            await to_thread(
                file_destination_path.parent.mkdir, parents=True, exist_ok=True
            )
            await to_thread(copyfile, file.path, file_destination_path)

        return f"betty-static:///file/{quote(file.id)}/file/{quote(file.name)}"
