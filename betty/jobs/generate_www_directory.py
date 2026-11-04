"""
Jobs to generate a site's WWW directories.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from typing import TYPE_CHECKING, Final, final, override

from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateWwwDirectory(Job):
    """
    Generate the WWW directory or directories.
    """

    __slots__ = ("_project",)

    id_for: Final[str] = "generate-www-directory"
    """
    The job ID.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for)
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(
            *(
                to_thread(
                    self._project.localize_www_directory(locale.locale).mkdir,
                    parents=True,
                )
                for locale in self._project.locales
            )
        )
