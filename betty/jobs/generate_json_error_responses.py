"""
Jobs to generate JSON error responses.
"""

from __future__ import annotations

from asyncio import to_thread
from json import dumps
from typing import TYPE_CHECKING, final, override

from betty.file import write
from betty.job import Job
from betty.json_schemas.project import ProjectSchema
from betty.localizables.gettext import _
from betty.localizer import default_localizer

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateJsonErrorResponses(Job):
    """
    Generate JSON HTTP error responses.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-error-responses"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        codes = [
            (401, _("I'm sorry, dear, but it seems you're not logged in.")),
            (
                403,
                _(
                    "I'm sorry, dear, but it seems you're not allowed to view this page."
                ),
            ),
            (404, _("I'm sorry, dear, but it seems this page does not exist.")),
        ]
        for locale in self._project.locales.keys():  # noqa: SIM118
            directory = self._project.localize_www_directory(locale) / ".error"
            for code, message in codes:
                await to_thread(directory.mkdir, exist_ok=True, parents=True)
                await write(
                    directory / f"{code}.json",
                    dumps({
                        "$schema": await ProjectSchema.def_url(
                            self._project, "errorResponse"
                        ),
                        "message": message.localize(default_localizer),
                    }),
                )
