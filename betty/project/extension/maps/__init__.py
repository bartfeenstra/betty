"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.locale.localizable.gettext import _
from betty.project.extension import ExtensionDefinition
from betty.project.extension.maps.jobs import _GeneratePlacePreviews
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.factory import ProjectDependentSelfFactory
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext


@final
@ExtensionDefinition(
    "maps",
    label="Maps",
    description=_("Display interactive maps"),
    depends_on={Webpack},
    assets_directory_path=Path(__file__).parent / "assets",
)
class Maps(Generator, EntryPointProvider, ProjectDependentSelfFactory):
    """
    Provide interactive maps for use on web pages.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GeneratePlacePreviews())
