"""
Jobs for the Webpack extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.job import Job
from betty.project import ProjectContext
from betty.project.extension.webpack import Webpack

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


class _GenerateAssets(Job[ProjectContext]):
    def __init__(self):
        super().__init__("webpack:generate-assets", priority=True)

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        extensions = await project.extensions
        webpack = extensions[Webpack]
        build_directory_path = await webpack._generate_ensure_build_directory(
            job_context=context
        )
        context._webpack_build_directory_path = build_directory_path  # type: ignore[attr-defined]
        await webpack._copy_build_directory(
            build_directory_path, project.www_directory_path
        )
