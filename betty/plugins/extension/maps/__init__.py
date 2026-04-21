"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.extension import Extension, ExtensionDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset.maps import MAPS
from betty.plugins.extension.maps.jobs import _GeneratePlacePreviews
from betty.plugins.extension.webpack import Webpack
from betty.plugins.webpack_entry_point.maps import Maps as MapsWebpackEntryPoint
from betty.project import Project
from betty.project.generate import Generator

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@ExtensionDefinition(
    "maps",
    label="Maps",
    description=_("Display interactive maps"),
    requires={
        Project.assets.require(MAPS),
        Project.extensions.require(Webpack.entry_points.require(MapsWebpackEntryPoint)),
    },
)
class Maps(Generator, Extension, Manufacturable):
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
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(_GeneratePlacePreviews(project=self._project))
