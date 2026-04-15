"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from asyncio import gather, to_thread
from contextlib import suppress
from math import ceil
from os import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING

from betty.concurrent import MAX_STRANDS
from betty.job import Context
from betty.job.executor.threading import ThreadPoolExecutor
from betty.job.scheduler.default import DefaultScheduler
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
    async def generate(self, scheduler: Scheduler) -> None:
        """
        Generate (part of) a project's site.
        """


async def generate(project: Project, *, context: Context | None = None) -> None:
    """
    Generate a new site.
    """
    if context is None:
        context = Context()

    await context.progress.add(2)

    await _preprocess(project)
    await context.progress.done()

    threading_concurrency = cpu_count() or 2
    scheduler = DefaultScheduler(context=context, user=project.upstream.user)
    async with ThreadPoolExecutor(
        scheduler,
        async_concurrency=ceil(MAX_STRANDS / threading_concurrency),
        threading_concurrency=threading_concurrency,
    ):
        await gather(
            *(
                extension.generate(scheduler)
                for extension in await project.extensions
                if isinstance(extension, Generator)
            )
        )
        await scheduler.release()
        await scheduler.add(
            GenerateStaticPublicAssets(project=project),
            GenerateSitemap(project=project),
            GenerateRobotsTxt(project=project),
            GenerateOpenApi(project=project),
            GenerateLocalizedPublicAssets(project=project),
            GenerateJsonSchema(project=project),
            GenerateJsonErrorResponses(project=project),
            GenerateFavicon(project=project),
            GenerateEntityTypesJson(project=project),
            GenerateEntityTypesHtml(project=project),
            GenerateEntitiesJson(project=project),
            GenerateEntitiesHtml(project=project),
        )
        await scheduler.complete()

    await _postprocess(project)
    await context.progress.done()


async def _preprocess(project: Project) -> None:
    await _preprocess_output_directory(project.output_directory)
    await _preprocess_www_directory(project.www_directory)


async def _preprocess_output_directory(output_directory_path: Path) -> None:
    with suppress(FileNotFoundError):
        await asyncio.to_thread(shutil.rmtree, output_directory_path)
    await to_thread(output_directory_path.mkdir, exist_ok=True, parents=True)


async def _preprocess_www_directory(www_directory_path: Path) -> None:
    await to_thread(www_directory_path.mkdir, exist_ok=True, parents=True)


async def _postprocess(project: Project) -> None:
    await _postprocess_output_directory(project.output_directory)


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
