"""
The ancestry data loading API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather
from typing import TYPE_CHECKING, final, override

from betty.concurrent import MAX_STRANDS
from betty.definition.human_facing import HumanFacingDefinition
from betty.job import Context
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin import ServicePluginDefinition

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


class Loader(ABC, Plugin["LoaderDefinition"]):
    """
    An ancestry data loader.
    """

    @abstractmethod
    async def load(self, scheduler: Scheduler) -> None:
        """
        Load ancestry data.
        """


@final
@PluginTypeDefinition(
    "loader",
    label=_("Loader"),
    label_plural=_("Loaders"),
    label_countable=ngettext("{count} loader", "{count} loaders"),
)
class LoaderDefinition(HumanFacingDefinition, ServicePluginDefinition[Loader]):
    """
    .. plugin_type:: loader.
    """


@final
class LoaderManufacturer(PluginManufacturer[LoaderDefinition, Loader]):
    """
    The loader manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[LoaderDefinition]:
        return LoaderDefinition


class Enricher(ABC, Plugin["EnricherDefinition"]):
    """
    An ancestry data enricher.
    """

    @abstractmethod
    async def enrich(self, scheduler: Scheduler) -> None:
        """
        Enrich ancestry data.
        """


@final
@PluginTypeDefinition(
    "enricher",
    label=_("Enricher"),
    label_plural=_("Enrichers"),
    label_countable=ngettext("{count} enricher", "{count} enrichers"),
)
class EnricherDefinition(HumanFacingDefinition, ServicePluginDefinition[Enricher]):
    """
    .. plugin_type:: enricher.
    """


@final
class EnricherManufacturer(PluginManufacturer[EnricherDefinition, Enricher]):
    """
    The enricher manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[EnricherDefinition]:
        return EnricherDefinition


async def load(project: Project, *, context: Context | None = None) -> None:
    """
    Load an ancestry.
    """
    if context is None:
        context = Context()

    await _do_jobs(
        project,
        context,
        LoaderDefinition,
        lambda scheduler, loader: loader.load(scheduler),
    )
    await _do_jobs(
        project,
        context,
        EnricherDefinition,
        lambda scheduler, enricher: enricher.enrich(scheduler),
    )


async def _do_jobs(
    project: Project,
    context: Context,
    plugin_type: type[ServicePluginDefinition],
    callback,
) -> None:
    scheduler = DefaultScheduler(context=context, user=project.upstream.user)
    async with AsyncExecutor(scheduler, concurrency=MAX_STRANDS):
        await gather(
            *(
                callback(scheduler, plugin)
                for plugin in (await project.service_plugins)[plugin_type]
            )
        )
        await scheduler.release()
        await scheduler.complete()
