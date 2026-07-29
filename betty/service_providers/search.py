"""
The Search extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.dirs import webpack_entry_point_directory
from betty.jobs.generate_search import GenerateSearch
from betty.localizables.gettext import _
from betty.project import Project
from betty.project.generate import Generator
from betty.service_provider import ServiceProvider, ServiceProviderDefinition
from betty.service_providers.webpack import Webpack
from betty.service_providers.webpack.build import EntryPointProvider

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath


@final
@ServiceProviderDefinition(
    "search",
    label=_("Search"),
    requires={
        Project.service_providers.require(Webpack),
    },
)
class Search(Generator, EntryPointProvider, ServiceProvider):
    """
    .. plugin:: extension:search.
    """

    def __init__(self, *, project: Project):
        super().__init__(services=project)
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(
            GenerateSearch(project=self._project),
        )

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
