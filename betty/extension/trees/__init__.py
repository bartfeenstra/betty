"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.extension import ExtensionDefinition
from betty.extension.trees.jobs import _GeneratePeopleJson
from betty.extension.webpack import Webpack
from betty.extension.webpack.build import EntryPointProvider
from betty.locale.localizable.gettext import _
from betty.project.generate import Generator
from betty.service.level import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project
    from betty.project.job import ProjectContext


@final
@ExtensionDefinition(
    "trees",
    label="Trees",
    description=_("Display interactive family trees using Cytoscape."),
    depends_on={Webpack},
    assets_directory=Path(__file__).parent / "assets",
)
class Trees(Generator, EntryPointProvider, Manufacturable):
    """
    .. plugin:: extension:trees.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, *, project: Project) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GeneratePeopleJson())

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
