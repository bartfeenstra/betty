"""
Jobs to publish :py:class:`betty.entities.file.File`'s files.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from shutil import copyfile
from typing import TYPE_CHECKING, Final, final, override
from urllib.parse import quote

from betty.job import Job
from betty.jobs.generate_entity import GenerateEntity

if TYPE_CHECKING:
    from pathlib import Path

    from betty.entities.file import File
    from betty.job.scheduler import Scheduler


def url(file: File, /) -> str:
    """
    Get the URL resource for a file.
    """
    return f"betty-static:///file/{quote(file.id)}/file/{quote(file.name)}"


@final
class GenerateFiles(Job):
    """
    Publish :py:class:`betty.entities.file.File`'s files.
    """

    id_for: Final[str] = "generate-files"
    """
    The job ID.
    """

    def __init__(self, *files: File, www_directory: Path):
        super().__init__(
            self.id_for, dependencies=map(GenerateEntity.id_for, files), priority=True
        )
        self._files = files
        self._file_directory = www_directory / "file"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(*(to_thread(self._do, file) for file in self._files))

    def _do(self, file: File, /) -> None:
        destination = self._file_directory / file.id / "file" / file.name
        # For monolingual sites, these paths overlap with those created by
        # :py:class:`betty.jobs.generate_entity.GenerateEntity`, but not for multilingual sites. We therefore try to
        # create all missing parents, but also allow the directory to exist already.
        destination.parent.mkdir(exist_ok=True, parents=True)
        copyfile(file.path, destination)
