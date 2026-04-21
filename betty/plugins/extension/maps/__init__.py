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
        # @todo Rethink our DX, composability, and where the responsibilities lie.
        # @todo
        # @todo 'Nested' plugin services should not have to know about extensions, e.g. Webpack entry points
        # @todo should just be any old service that does not need special casing to be put onto an extension.
        # @todo
        # @todo That also means PluginServiceRequirement is of limited use as it cannot get the correct service provider
        # @todo from the service level.
        # @todo
        # @todo Either way, PluginServiceInitializer will need knowledge of how to handle plugin services on extensions
        # @todo
        # @todo Which means putting everything in the extension API is really not necessary.
        # @todo Can we merge this all into PluginServiceRequirement?
        # @todo Or at least move it closer to the core APIs?
        # @todo
        # @todo
        Project.extensions.require(Webpack.entry_points.require(MapsWebpackEntryPoint)),
        # @todo Alternatively... (but I don't like the inside-out appearance, it reads badly)
        # @todo However, this may be the only format that lets us get the value of the inner service
        # @todo when calling the requirement.
        Webpack.entry_points.require(Project.extensions, MapsWebpackEntryPoint),
        # @todo Alternatively...
        # @todo Actually, this could return the inner service's value as well.
        Project.extensions.require(Webpack.entry_points, MapsWebpackEntryPoint),
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
