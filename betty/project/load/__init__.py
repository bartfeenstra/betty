"""
Provide the Ancestry loading API.
"""

from abc import ABC, abstractmethod
from asyncio import gather

from betty.ancestry.link import Link
from betty.concurrent import MAX_STRANDS
from betty.job import Context
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler import Scheduler
from betty.job.scheduler.default import DefaultScheduler
from betty.project import Project
from betty.project.load.jobs import PopulateLink


class Loader(ABC):
    """
    Load ancestry data into a project.
    """

    @abstractmethod
    async def load(self, scheduler: Scheduler) -> None:
        """
        Load ancestry data into a project.
        """


class PostLoader(ABC):
    """
    Postprocess ancestry data after it has been loaded.
    """

    @abstractmethod
    async def post_load(self, scheduler: Scheduler) -> None:
        """
        Postprocess ancestry data after it has been loaded.
        """


async def load(project: Project, *, context: Context | None = None) -> None:
    """
    Load an ancestry.
    """
    if context is None:
        context = Context()

    app = project.app
    http_client = await app.http_client
    localizers = await project.public_localizers

    extensions = await project.extensions
    load_scheduler = DefaultScheduler(context=context, user=project.app.user)
    async with AsyncExecutor(load_scheduler, concurrency=MAX_STRANDS):
        await gather(
            *(
                extension.load(load_scheduler)
                for extension in extensions
                if isinstance(extension, Loader)
            )
        )
        await load_scheduler.release()
        await load_scheduler.complete()
    post_load_scheduler = DefaultScheduler(context=context, user=project.app.user)
    async with AsyncExecutor(post_load_scheduler, concurrency=MAX_STRANDS):
        await gather(
            *(
                extension.post_load(post_load_scheduler)
                for extension in extensions
                if isinstance(extension, PostLoader)
            )
        )
        await post_load_scheduler.release()
        await post_load_scheduler.add(
            *(
                PopulateLink(link, http_client=http_client, localizers=localizers)
                for link in project.ancestry[Link]
            ),
        )
        await post_load_scheduler.complete()
