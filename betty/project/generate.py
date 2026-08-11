"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import shutil
from abc import ABCMeta, abstractmethod
from asyncio import gather, to_thread
from contextlib import suppress
from math import ceil
from os import cpu_count
from typing import TYPE_CHECKING

from betty.concurrent import max_strands
from betty.job import Context
from betty.job.executor.threading import ThreadPoolExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.jobs.generate_entities_html import GenerateEntitiesHtml
from betty.jobs.generate_entities_json import GenerateEntitiesJson
from betty.jobs.generate_entity_types_html import GenerateEntityTypesHtml
from betty.jobs.generate_entity_types_json import GenerateEntityTypesJson
from betty.jobs.generate_favicon import GenerateFavicon
from betty.jobs.generate_json_error_responses import GenerateJsonErrorResponses
from betty.jobs.generate_json_schema import GenerateJsonSchema
from betty.jobs.generate_localized_public_assets import GenerateLocalizedPublicAssets
from betty.jobs.generate_openapi import GenerateOpenapi
from betty.jobs.generate_robots_txt import GenerateRobotsTxt
from betty.jobs.generate_sitemap import GenerateSitemap
from betty.jobs.generate_static_public_assets import GenerateStaticPublicAssets

if TYPE_CHECKING:
    from pathlib import Path

    from betty.job.scheduler import Scheduler
    from betty.project import Project


class Generator(metaclass=ABCMeta):
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

    async with context.progress:
        await _preprocess(project)

    threading_concurrency = cpu_count() or 2
    scheduler = DefaultScheduler(context=context, user=project.upstream.user)
    async with ThreadPoolExecutor(
        scheduler,
        async_concurrency=ceil(max_strands / threading_concurrency),
        threading_concurrency=threading_concurrency,
    ):
        await gather(*[
            service_provider.generate(scheduler)
            for service_provider in await gather(*project.service_providers)
            if isinstance(service_provider, Generator)
        ])
        await scheduler.release()
        await scheduler.add(
            GenerateStaticPublicAssets(project=project),
            GenerateSitemap(project=project),
            GenerateRobotsTxt(project=project),
            GenerateOpenapi(project=project),
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


async def _preprocess(project: Project) -> None:
    await _preprocess_output_directory(project.output_directory)
    await _preprocess_www_directory(project.www_directory)


async def _preprocess_output_directory(output_directory: Path, /) -> None:
    with suppress(FileNotFoundError):
        await asyncio.to_thread(shutil.rmtree, output_directory)
    await to_thread(output_directory.mkdir, exist_ok=True, parents=True)


async def _preprocess_www_directory(www_directory: Path, /) -> None:
    await to_thread(www_directory.mkdir, exist_ok=True, parents=True)


async def _postprocess(project: Project) -> None:
    await _postprocess_output_directory(project.output_directory)


async def _postprocess_output_directory(output_directory: Path, /) -> None:
    output_directory.chmod(0o755)
    for directory, subdirectory_names, file_names in output_directory.walk():
        for subdirectory_name in subdirectory_names:
            (directory / subdirectory_name).chmod(0o755)
        for file_name in file_names:
            (directory / file_name).chmod(0o644)
