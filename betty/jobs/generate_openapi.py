"""
Jobs to generate OpenAPI assets.
"""

from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, final, override

from betty.job import Job
from betty.jobs import _create_json_resource
from betty.openapi import Specification

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateOpenapi(Job):
    """
    Generate a site's OpenAPI specification.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-openapi"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await _create_json_resource(
            self._project.www_directory / "api",
            dumps(await Specification(self._project).build()),
        )
