"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.trees import TREES
from betty.dirs import WEBPACK_ENTRY_POINT_DIRECTORY
from betty.extension import ExtensionDefinition
from betty.extensions.trees.jobs import _GeneratePeopleJson
from betty.extensions.webpack import Webpack
from betty.extensions.webpack.build import EntryPointProvider
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath


@final
@ExtensionDefinition(
    "trees",
    label="Trees",
    description=_("Display interactive family trees using Cytoscape."),
    requires={
        Project.asset_directories.require(TREES),
        Project.extensions.require(Webpack),
    },
)
class Trees(Generator, EntryPointProvider, Manufacturable):
    """
    .. plugin:: extension:trees.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GeneratePeopleJson(project=self._project))

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return WEBPACK_ENTRY_POINT_DIRECTORY / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
