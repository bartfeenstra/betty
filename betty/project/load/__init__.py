"""
Provide the Ancestry loading API.
"""

from abc import ABC, abstractmethod
from asyncio import gather
from math import ceil
from os import cpu_count

from betty.ancestry.link import Link
from betty.concurrent import MAX_STRANDS
from betty.job.executor.threading import ThreadPoolExecutor
from betty.job.scheduler import Scheduler
from betty.job.scheduler.default import DefaultScheduler
from betty.project import Project, ProjectContext
from betty.project.load.jobs import PopulateLink


class Loader(ABC):
    """
    Load ancestry data into a project.
    """

    @abstractmethod
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        """
        Load ancestry data into a project.
        """


class PostLoader(ABC):
    """
    Postprocess ancestry data after it has been loaded.
    """

    @abstractmethod
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        """
        Postprocess ancestry data after it has been loaded.
        """


async def load(project: Project, *, job_context: ProjectContext | None = None) -> None:
    """
    Load an ancestry.
    """
    if job_context is None:
        job_context = ProjectContext(project)

    extensions = await project.extensions
    threading_concurrency = cpu_count() or 2
    async_concurrency = ceil(MAX_STRANDS / threading_concurrency)
    load_scheduler = DefaultScheduler(
        job_context, progress=job_context.progress, user=project.app.user
    )
    async with ThreadPoolExecutor(
        load_scheduler,
        async_concurrency=async_concurrency,
        threading_concurrency=threading_concurrency,
    ):
        await gather(
            *(
                extension.load(load_scheduler)
                for extensions in extensions
                for extension in extensions
                if isinstance(extension, Loader)
            )
        )
        await load_scheduler.release()
        await load_scheduler.complete()
    post_load_scheduler = DefaultScheduler(
        job_context, progress=job_context.progress, user=project.app.user
    )
    async with ThreadPoolExecutor(
        post_load_scheduler,
        async_concurrency=async_concurrency,
        threading_concurrency=threading_concurrency,
    ):
        await gather(
            *(
                extension.post_load(post_load_scheduler)
                for extensions in extensions
                for extension in extensions
                if isinstance(extension, PostLoader)
            )
        )
        await post_load_scheduler.release()
        await post_load_scheduler.add(
            *(PopulateLink(link) for link in project.ancestry[Link]),
        )
        await post_load_scheduler.complete()
    project.ancestry.immutable()
