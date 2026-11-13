"""
Provide the Generation API.
"""

from __future__ import annotations

import shutil
from abc import ABCMeta, abstractmethod
from asyncio import gather, to_thread
from contextlib import suppress
from math import ceil
from os import cpu_count
from typing import TYPE_CHECKING

from betty.concurrent import max_strands
from betty.entity import EntityDefinition
from betty.job import Context, Job
from betty.job.executor.threading import ThreadPoolExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.jobs.generate_entity import GenerateEntity
from betty.jobs.generate_entity_html import GenerateEntityHtml
from betty.jobs.generate_entity_type import GenerateEntityType
from betty.jobs.generate_entity_type_html import GenerateEntityTypeHtml
from betty.jobs.generate_favicon import GenerateFavicon
from betty.jobs.generate_public_assets import (
    GenerateLocalizedPublicAssets,
    GenerateStaticPublicAssets,
)
from betty.jobs.generate_robots_txt import GenerateRobotsTxt
from betty.jobs.generate_sitemap import GenerateSitemap
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

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

    # Track preprocessing and postprocessing.
    await context.progress.add(2)

    await to_thread(_preprocess, project)
    await context.progress.done()

    threading_concurrency = cpu_count() or 2
    scheduler = DefaultScheduler(context=context, ui=project.upstream.ui)
    async with ThreadPoolExecutor(
        scheduler,
        async_concurrency=ceil(max_strands / threading_concurrency),
        threading_concurrency=threading_concurrency,
    ):
        await scheduler.add(*[job async for job in _builtin_jobs(project)])
        await gather(*[
            service_provider.generate(scheduler)
            for service_provider in await gather(*project.service_providers)
            if isinstance(service_provider, Generator)
        ])
        await scheduler.release()
        await scheduler.complete()

    await to_thread(_postprocess, project)
    await context.progress.done()


async def _builtin_jobs(project: Project, /) -> AsyncIterator[Job]:
    yield GenerateWwwDirectory(project=project)
    yield GenerateStaticPublicAssets(project=project)
    yield GenerateLocalizedPublicAssets(project=project)
    yield GenerateSitemap(project=project)
    yield GenerateRobotsTxt(project=project)
    yield GenerateFavicon(project=project)
    async for entity_type in project.plugins[EntityDefinition]:
        if entity_type.public_facing:
            yield GenerateEntityType(entity_type, project=project)
            if entity_type.id in project.generate_entity_list_html:
                yield GenerateEntityTypeHtml(entity_type, project=project)
            for entity in project.ancestry[entity_type.cls]:
                yield GenerateEntity(entity, project=project)
                if entity_type.public_facing and entity.id.persistent and entity.public:
                    yield GenerateEntityHtml(entity, project=project)


def _preprocess(project: Project) -> None:
    with suppress(FileNotFoundError):
        shutil.rmtree(project.output_directory)
    project.output_directory.mkdir(parents=True)


def _postprocess(project: Project) -> None:
    project.output_directory.chmod(0o755)
    for directory, subdirectory_names, file_names in project.output_directory.walk():
        for subdirectory_name in subdirectory_names:
            (directory / subdirectory_name).chmod(0o755)
        for file_name in file_names:
            (directory / file_name).chmod(0o644)
