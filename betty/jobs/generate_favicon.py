"""
Jobs to generate favicons.
"""

from __future__ import annotations

from asyncio import to_thread
from io import BytesIO
from typing import TYPE_CHECKING, final, override

from PIL import Image

from betty.file import read, write
from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateFavicon(Job):
    """
    Generate a site's favicon.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-favicon"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await to_thread(self._project.www_directory.mkdir, exist_ok=True, parents=True)
        logo = BytesIO(await read(self._project.logo, mode="rb"))
        image = Image.open(logo)
        favicon = BytesIO()
        image.save(favicon, format="ICO")
        await write(
            self._project.www_directory / "favicon.ico", favicon.getvalue(), mode="wb"
        )
