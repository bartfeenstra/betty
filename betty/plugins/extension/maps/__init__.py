"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.maps import MAPS
from betty.dirs import WEBPACK_ENTRY_POINT_DIRECTORY
from betty.extension import ExtensionDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.extension.maps.jobs import _GeneratePlacePreviews
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.project import Project
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath


@final
@ExtensionDefinition(
    "maps",
    label="Maps",
    description=_("Display interactive maps"),
    requires={
        Project.asset_directories.require(MAPS),
        Project.extensions.require(Webpack),
    },
)
class Maps(Generator, EntryPointProvider, Manufacturable):
    """
    .. plugin:: extension:maps.
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
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return WEBPACK_ENTRY_POINT_DIRECTORY / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GeneratePlacePreviews(project=self._project))
