"""
Jobs to generate project logos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.job import Job
from betty.os import link_or_copy

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateLogo(Job):
    """
    Generate the project logo.
    """

    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-logo")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await link_or_copy(
            self._project.logo,
            self._project.www_directory / ("logo" + self._project.logo.suffix),
        )
