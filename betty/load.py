"""
The ancestry data loading API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import gather
from functools import partial
from typing import TYPE_CHECKING, final

from betty.concurrent import max_strands
from betty.definition.human_facing import HumanFacingDefinition
from betty.job import Context
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import (
    ClassedPluginDefinition,
    ConfigurablePluginFactory,
    NewPlugin,
    Plugin,
)
from betty.plugin.config import ConfigurablePluginDefinition
from betty.plugin.factory import NewPluginDefinition

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection

    from betty.data import Data
    from betty.job.scheduler import Scheduler
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires


class Loader(Plugin["LoaderDefinition"], metaclass=ABCMeta):
    """
    An ancestry data loader.
    """

    @abstractmethod
    async def load(self, scheduler: Scheduler, /) -> None:
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
class LoaderDefinition(HumanFacingDefinition, ClassedPluginDefinition[Loader]):
    """
    .. plugin_type:: loader.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        auto: bool = False,
        config_cls: type[Data] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            config_cls=config_cls,
            description=description,
            label=label,
            requires=requires,
        )


@final
@NewPluginDefinition(LoaderDefinition)
class NewLoader(NewPlugin[LoaderDefinition, Loader]):
    """
    The loader factory.
    """


type LoaderFactory[PluginT: Loader, ConfigT: Data] = ConfigurablePluginFactory[
    PluginT, NewLoader, ConfigT
]


class Enricher(Plugin["EnricherDefinition"], metaclass=ABCMeta):
    """
    An ancestry data enricher.
    """

    @abstractmethod
    async def enrich(self, scheduler: Scheduler, /) -> None:
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
class EnricherDefinition(HumanFacingDefinition, ConfigurablePluginDefinition[Enricher]):
    """
    .. plugin_type:: enricher.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        auto: bool = False,
        config_cls: type[Data] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            config_cls=config_cls,
            description=description,
            label=label,
            requires=requires,
        )


@final
@NewPluginDefinition(EnricherDefinition)
class NewEnricher(NewPlugin[EnricherDefinition, Enricher]):
    """
    The enricher factory.
    """


type EnricherFactory[PluginT: Enricher, ConfigT: Data] = ConfigurablePluginFactory[
    PluginT, NewEnricher, ConfigT
]


async def load(project: Project, *, context: Context | None = None) -> None:
    """
    Load an ancestry.
    """
    if context is None:
        context = Context()

    await _do_jobs(
        project,
        context,
        await gather(*project.loaders),
        lambda scheduler, loader: loader.load(scheduler),
    )
    await _do_jobs(
        project,
        context,
        await gather(*project.enrichers),
        lambda scheduler, enricher: enricher.enrich(scheduler),
    )


async def _do_jobs[PluginT: Plugin](
    project: Project,
    context: Context,
    plugins: Collection[PluginT],
    callback: Callable[[Scheduler, PluginT], Awaitable[None]],
) -> None:
    scheduler = DefaultScheduler(context=context, user=project.upstream.user)
    async with AsyncExecutor(scheduler, concurrency=max_strands):
        await gather(*map(partial(callback, scheduler), plugins))
        await scheduler.release()
        await scheduler.complete()
