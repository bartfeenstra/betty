"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.extension import Extension, ExtensionDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset.trees import TREES
from betty.plugins.extension.trees.jobs import _GeneratePeopleJson
from betty.plugins.extension.webpack import Webpack
from betty.plugins.webpack_entry_point.trees import Trees as TreesWebpackEntryPoint
from betty.project import Project
from betty.project.generate import Generator

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@ExtensionDefinition(
    "trees",
    label="Trees",
    description=_("Display interactive family trees using Cytoscape."),
    requires={
        Project.assets.require(TREES),
        Project.extensions.require(Webpack.entry_points, TreesWebpackEntryPoint),
    },
)
class Trees(Generator, Extension, Manufacturable):
    """
    .. plugin:: extension:trees.
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
        await scheduler.add(_GeneratePeopleJson(project=self.services))
