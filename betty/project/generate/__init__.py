"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from asyncio import gather
from contextlib import suppress
from math import ceil
from os import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING

from aiofiles.os import makedirs

from betty.concurrent import MAX_STRANDS
from betty.job.executor.threading import ThreadPoolExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.project import ProjectContext
from betty.project.generate.jobs import (
    GenerateEntitiesHtml,
    GenerateEntitiesJson,
    GenerateEntityTypesHtml,
    GenerateEntityTypesJson,
    GenerateFavicon,
    GenerateJsonErrorResponses,
    GenerateJsonSchema,
    GenerateLocalizedPublicAssets,
    GenerateOpenApi,
    GenerateRobotsTxt,
    GenerateSitemap,
    GenerateStaticPublicAssets,
)

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


class Generator(ABC):
    """
    Generate (part of) a project's site.
    """

    @abstractmethod
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        """
        Generate (part of) a project's site.
        """


async def generate(
    project: Project, *, job_context: ProjectContext | None = None
) -> None:
    """
    Generate a new site.
    """
    if job_context is None:
        job_context = ProjectContext(project)

    await job_context.progress.add(2)

    await _preprocess(project)
    await job_context.progress.done()

    threading_concurrency = cpu_count() or 2
    scheduler = DefaultScheduler(
        job_context, progress=job_context.progress, user=project.app.user
    )
    async with ThreadPoolExecutor(
        scheduler,
        async_concurrency=ceil(MAX_STRANDS / threading_concurrency),
        threading_concurrency=threading_concurrency,
    ):
        await gather(
            *(
                extension.generate(scheduler)
                for extensions in await project.extensions
                for extension in extensions
                if isinstance(extension, Generator)
            )
        )
        await scheduler.release()
        await scheduler.add(
            GenerateStaticPublicAssets(),
            GenerateSitemap(),
            GenerateRobotsTxt(),
            GenerateOpenApi(),
            GenerateLocalizedPublicAssets(),
            GenerateJsonSchema(),
            GenerateJsonErrorResponses(),
            GenerateFavicon(),
            GenerateEntityTypesJson(),
            GenerateEntityTypesHtml(),
            GenerateEntitiesJson(),
            GenerateEntitiesHtml(),
        )
        await scheduler.complete()

    await _postprocess(project)
    await job_context.progress.done()


async def _preprocess(project: Project) -> None:
    await _preprocess_output_directory(project.configuration.output_directory_path)
    await _preprocess_www_directory(project.configuration.www_directory_path)


async def _preprocess_output_directory(output_directory_path: Path) -> None:
    with suppress(FileNotFoundError):
        await asyncio.to_thread(shutil.rmtree, output_directory_path)
    await makedirs(output_directory_path, exist_ok=True)


async def _preprocess_www_directory(www_directory_path: Path) -> None:
    await makedirs(www_directory_path, exist_ok=True)


async def _postprocess(project: Project) -> None:
    await _postprocess_output_directory(project.configuration.output_directory_path)


async def _postprocess_output_directory(output_directory_path: Path) -> None:
    output_directory_path.chmod(0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(
        output_directory_path
    ):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            (directory_path / subdirectory_name).chmod(0o755)
        for file_name in file_names:
            (directory_path / file_name).chmod(0o644)
