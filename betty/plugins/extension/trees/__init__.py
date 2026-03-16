"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from betty.asset import AssetDefinition
from betty.extension import ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.trees import Trees as TreesAsset
from betty.plugins.extension.trees.jobs import _GeneratePeopleJson
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.project.generate import Generator
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
@ExtensionDefinition(
    "trees",
    label="Trees",
    description=_("Display interactive family trees using Cytoscape."),
    requires={AssetDefinition: TreesAsset, ExtensionDefinition: Webpack},
)
class Trees(Generator, EntryPointProvider, Manufacturable):
    """
    .. plugin:: extension:trees.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GeneratePeopleJson(project=self._project))

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
