"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.maps import maps
from betty.dirs import webpack_entry_point_directory
from betty.factory import Arg1Manufacturable
from betty.jobs._generate_maps_place_previews import _GenerateMapsPlacePreviews
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
    "maps",
    label="Maps",
    description=_("Display interactive maps"),
    requires={
        Project.asset_directories.require(maps),
        Project.service_providers.require(Webpack),
    },
)
class Maps(Generator, EntryPointProvider[Project], Arg1Manufacturable[Project]):
    """
    .. plugin:: service-provider:maps.
    """

    def __init__(self, *, project: Project):
        super().__init__(services=project)

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GenerateMapsPlacePreviews(project=self.services))
