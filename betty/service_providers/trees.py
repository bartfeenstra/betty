"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.trees import trees
from betty.dirs import webpack_entry_point_directory
from betty.factory import Arg1Manufacturable
from betty.jobs._generate_trees_people_json import _GenerateTreesPeopleJson
from betty.localizables.gettext import _
from betty.project import Project
from betty.project.generate import Generator
from betty.service_provider import ServiceProviderDefinition
from betty.service_providers.webpack import Webpack
from betty.service_providers.webpack.build import EntryPointProvider

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath


@final
@ServiceProviderDefinition(
    "trees",
    label="Trees",
    description=_("Display interactive family trees using Cytoscape."),
    requires={
        Project.asset_directories.require(trees),
        Project.service_providers.require(Webpack),
    },
)
class Trees(Generator, EntryPointProvider[Project], Arg1Manufacturable[Project]):
    """
    .. plugin:: service-provider:trees.
    """

    def __init__(self, *, project: Project):
        super().__init__(services=project)

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GenerateTreesPeopleJson(project=self.services))

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
