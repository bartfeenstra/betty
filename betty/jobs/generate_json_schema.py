"""
Jobs to generate JSON schemas for projects.
"""

from __future__ import annotations

from asyncio import to_thread
from json import dumps
from typing import TYPE_CHECKING, final, override

from betty.file import write
from betty.job import Job
from betty.json_schemas.project import new_project_schema, project_schema_www_path

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateJsonSchema(Job):
    """
    Generate the JSON schema for a projects.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-schema"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        schema_file = project_schema_www_path(self._project)
        await to_thread(schema_file.parent.mkdir, exist_ok=True, parents=True)
        await write(schema_file, dumps(await new_project_schema(self._project)))
