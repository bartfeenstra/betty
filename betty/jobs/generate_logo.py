"""
Jobs to generate project logos.
"""

from __future__ import annotations

from asyncio import to_thread
from shutil import copyfile
from typing import TYPE_CHECKING, final, override

from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateLogo(Job):
    """
    Generate the project logo.
    """

    def __init__(self, *, project: Project):
        super().__init__("generate-logo", dependencies=[GenerateWwwDirectory.id_for])
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await to_thread(
            copyfile,
            self._project.logo,
            self._project.www_directory / ("logo" + self._project.logo.suffix),
        )
