"""
Jobs to generate favicons.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Final, final, override

from PIL import Image

from betty.file import read, write
from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateFavicon(Job):
    """
    Generate a site's favicon.
    """

    id_for: Final[str] = "generate-favicon"
    """
    The job ID.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for, dependencies=[GenerateWwwDirectory.id_for])
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        logo = BytesIO(await read(self._project.logo, mode="rb"))
        image = Image.open(logo)
        favicon = BytesIO()
        image.save(favicon, format="ICO")
        await write(
            self._project.www_directory / "favicon.ico", favicon.getvalue(), mode="wb"
        )
